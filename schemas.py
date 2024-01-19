from typing import Literal
from pydantic import BaseModel


class RegisterSchema(BaseModel):
    username: str
    password: str


class LoginSchema(BaseModel):
    username: str
    password: str


class RefreshSchema(BaseModel):
    refresh_token: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class BaseSchema(BaseModel):
    id: int


class UserSchema(BaseSchema):
    username: str


class PartialCourseSchema(BaseSchema):
    course_id: str #課程代碼
    course_class: str #開課班別
    course_zh_name: str #中文名稱
    course_en_name: str #英文名稱
    course_syllabus: str #教學大綱
    course_type1: str #課程性質1
    course_type2: str #課程性質2
    course_fully_eng: bool #全英文上課
    course_credit: int #學分
    course_teacher_name: str #教師姓名
    course_teacher_link: str #教師連結
    course_building: str #上課大樓
    course_time_and_loc: str #上課節次+地點
    course_student_limit: int #上限人數
    course_student_registered: int #登記人數
    course_student_selected: int #選上人數
    course_can_cross_class: str #可跨班
    course_note: str #備註


class PartialCourseWeekTimeSchema(BaseSchema):
    week: int
    time: int
    course_id: int


class CourseSchema(PartialCourseSchema):
    course_week_times: list[PartialCourseWeekTimeSchema] = []


class CourseWeekTimeSchema(PartialCourseWeekTimeSchema):
    course: PartialCourseSchema


class CourseQuerySchema(BaseModel):
    course_day_night: bool | None = None
    course_class: str | None = None
    course_name: str | None = None
    course_fully_eng: bool | None = None
    course_id: str | None = None
    course_time: Literal[0, 1, 2, 3, 4, 5, 6] | None = None
    course_teacher_name: str | None = None