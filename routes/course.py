from fastapi import Depends
from fastapi.routing import APIRouter

from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import Course, CourseWeekTime
from schemas import CourseSchema, CourseQuerySchema
from dependencies import get_db

router = APIRouter(prefix="/courses")

@router.get(path="", response_model=list[CourseSchema])
async def index(query: CourseQuerySchema = Depends(), db: Session = Depends(get_db)):
    sql_query = db.query(Course).join(CourseWeekTime, and_(Course.course_week_times, CourseWeekTime.is_disabled == False), isouter=True)
    if query.course_day_night is not None:
        sql_query = sql_query.filter(Course.course_day_night == query.course_day_night)
    if query.course_class is not None:
        sql_query = sql_query.filter(Course.course_class.contains(query.course_class))
    if query.course_fully_eng is not None:
        sql_query = sql_query.filter(Course.course_fully_eng == query.course_fully_eng)
    if query.course_id is not None:
        sql_query = sql_query.filter(Course.course_id.contains(query.course_id))
    if query.course_time is not None:
        sql_query = sql_query.filter(CourseWeekTime.week == query.course_time)
    if query.course_teacher_name is not None:
        sql_query = sql_query.filter(Course.course_teacher_name.contains(query.course_teacher_name))
    return sql_query.all()