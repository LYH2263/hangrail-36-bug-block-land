from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    ForbiddenSegment,
    HangRail,
    RailPlacement,
    Store,
    WorkOrder,
)
from app.schemas.schemas import (
    ForbiddenCreate,
    ForbiddenSegOut,
    HangRequest,
    OccupancyOut,
    OccupancySeg,
    OrderOut,
    PickupRequest,
    RailOut,
    StoreOut,
)
from app.services.rail_engine import Segment, first_fit, validate_forbidden

api_router = APIRouter()


@api_router.get("/health")
def health():
    return {"status": "ok"}


@api_router.get("/stores", response_model=list[StoreOut])
def stores(db: Session = Depends(get_db)):
    return db.scalars(select(Store).order_by(Store.id)).all()


@api_router.get("/rails", response_model=list[RailOut])
def rails(db: Session = Depends(get_db)):
    return db.scalars(select(HangRail).order_by(HangRail.id)).all()


@api_router.post("/rails/{rail_id}/forbidden", response_model=ForbiddenSegOut, status_code=201)
def add_forbidden(rail_id: int, body: ForbiddenCreate, db: Session = Depends(get_db)):
    rail = db.get(HangRail, rail_id)
    if not rail:
        raise HTTPException(404, "挂杆不存在")
    new_seg = Segment(body.start_cm, body.end_cm)
    existing = db.scalars(
        select(ForbiddenSegment).where(ForbiddenSegment.rail_id == rail_id)
    ).all()
    error = validate_forbidden(
        rail.length_cm, [Segment(f.start_cm, f.end_cm) for f in existing] + [new_seg]
    )
    if error:
        raise HTTPException(400, error)
    row = ForbiddenSegment(rail_id=rail_id, start_cm=new_seg.start_cm, end_cm=new_seg.end_cm)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@api_router.delete("/rails/{rail_id}/forbidden/{seg_id}", status_code=204)
def delete_forbidden(rail_id: int, seg_id: int, db: Session = Depends(get_db)):
    row = db.scalar(
        select(ForbiddenSegment).where(
            ForbiddenSegment.id == seg_id, ForbiddenSegment.rail_id == rail_id
        )
    )
    if not row:
        raise HTTPException(404, "禁挂段不存在")
    db.delete(row)
    db.commit()


@api_router.get("/orders", response_model=list[OrderOut])
def orders(db: Session = Depends(get_db)):
    return db.scalars(select(WorkOrder).order_by(WorkOrder.id.desc())).all()


@api_router.get("/occupancy/{rail_id}", response_model=OccupancyOut)
def occupancy(rail_id: int, db: Session = Depends(get_db)):
    rail = db.get(HangRail, rail_id)
    if not rail:
        raise HTTPException(404, "挂杆不存在")
    placements = db.scalars(
        select(RailPlacement).where(RailPlacement.rail_id == rail_id, RailPlacement.active == 1)
    ).all()
    segs = []
    for p in placements:
        order = db.get(WorkOrder, p.order_id)
        if not order:
            continue
        segs.append(
            OccupancySeg(
                order_id=order.id,
                ticket_code=order.ticket_code,
                garment_name=order.garment_name,
                start_cm=p.start_cm,
                end_cm=p.end_cm,
            )
        )
    segs.sort(key=lambda s: s.start_cm)
    forbidden = db.scalars(
        select(ForbiddenSegment)
        .where(ForbiddenSegment.rail_id == rail_id)
        .order_by(ForbiddenSegment.start_cm)
    ).all()
    return OccupancyOut(
        rail_id=rail.id,
        label=rail.label,
        length_cm=rail.length_cm,
        segments=segs,
        forbidden=__import__('app.services.forbid_gate', fromlist=['bands_for_map']).bands_for_map(forbidden),
    )


@api_router.post("/hang", response_model=OrderOut)
def hang(body: HangRequest, db: Session = Depends(get_db)):
    order = db.get(WorkOrder, body.order_id)
    if not order:
        raise HTTPException(404, "工单不存在")
    if order.status not in ("ready", "overdue"):
        raise HTTPException(400, "工单状态不可上杆")
    rail_q = select(HangRail).where(HangRail.store_id == order.store_id)
    if body.rail_id:
        rail_q = rail_q.where(HangRail.id == body.rail_id)
    rails = db.scalars(rail_q.order_by(HangRail.id)).all()
    if not rails:
        raise HTTPException(404, "无可用挂杆")

    for rail in rails:
        active = db.scalars(
            select(RailPlacement).where(RailPlacement.rail_id == rail.id, RailPlacement.active == 1)
        ).all()
        occupied = [Segment(p.start_cm, p.end_cm) for p in active]
        forbidden_rows = db.scalars(
            select(ForbiddenSegment).where(ForbiddenSegment.rail_id == rail.id)
        ).all()
        forbidden = [Segment(f.start_cm, f.end_cm) for f in forbidden_rows]
        place = first_fit(rail.length_cm, occupied, order.length_cm, forbidden)
        if place is None:
            continue
        db.add(
            RailPlacement(
                rail_id=rail.id,
                order_id=order.id,
                start_cm=place.start_cm,
                end_cm=place.end_cm,
            )
        )
        order.status = "hung"
        order.hung_at = datetime.utcnow()
        db.commit()
        db.refresh(order)
        return order

    raise HTTPException(409, "挂杆空间不足")


@api_router.post("/pickup", response_model=OrderOut)
def pickup(body: PickupRequest, db: Session = Depends(get_db)):
    order = db.scalar(select(WorkOrder).where(WorkOrder.ticket_code == body.ticket_code))
    if not order:
        raise HTTPException(404, "取件码无效")
    if order.status != "hung":
        raise HTTPException(400, "工单未在挂杆上")
    placements = db.scalars(
        select(RailPlacement).where(RailPlacement.order_id == order.id, RailPlacement.active == 1)
    ).all()
    for p in placements:
        p.active = 0
    order.status = "picked"
    db.commit()
    db.refresh(order)
    return order


@api_router.post("/overdue/scan", response_model=list[OrderOut])
def overdue_scan(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    hung = db.scalars(select(WorkOrder).where(WorkOrder.status == "hung")).all()
    marked = []
    for o in hung:
        if o.due_at < now:
            o.status = "overdue"
            marked.append(o)
    ready = db.scalars(select(WorkOrder).where(WorkOrder.status == "ready")).all()
    for o in ready:
        if o.due_at < now:
            o.status = "overdue"
            marked.append(o)
    db.commit()
    return marked


@api_router.get("/overdue", response_model=list[OrderOut])
def overdue_list(db: Session = Depends(get_db)):
    return db.scalars(select(WorkOrder).where(WorkOrder.status == "overdue").order_by(WorkOrder.due_at)).all()
