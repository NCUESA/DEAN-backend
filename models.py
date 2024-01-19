from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, SmallInteger, ForeignKey


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, unique=True, nullable=False, autoincrement=True)


class User(Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(length=20), index=True, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(length=100))

    selected_courses: Mapped[list["Course"]] = relationship("Course", secondary="user_course_maps", secondaryjoin="and_(UserCourseMap.user_id == User.id, UserCourseMap.is_disabled == False)", uselist=True)


class Course(Base):
    __tablename__ = "courses"
    course_id: Mapped[str] = mapped_column(String(length=10), unique=True, index=True, nullable=False) #課程代碼
    course_class: Mapped[str] = mapped_column(String(length=20)) #開課班別
    course_zh_name: Mapped[str] = mapped_column(String(length=100)) #中文名稱
    course_en_name: Mapped[str] = mapped_column(String(length=100)) #英文名稱
    course_syllabus: Mapped[str] = mapped_column(String(length=200), nullable=True) #教學大綱
    course_type1: Mapped[str] = mapped_column(String(length=20), nullable=True) #課程性質1
    course_type2: Mapped[str] = mapped_column(String(length=20), nullable=True) #課程性質2
    course_fully_eng: Mapped[bool] = mapped_column(Boolean) #全英文上課
    course_credit: Mapped[int] = mapped_column(SmallInteger) #學分
    course_teacher_name: Mapped[str] = mapped_column(String(length=20), nullable=True) #教師姓名
    course_teacher_link: Mapped[str] = mapped_column(String(length=200), nullable=True) #教師連結
    course_building: Mapped[str] = mapped_column(String(length=50), nullable=True) #上課大樓
    course_time_and_loc: Mapped[str] = mapped_column(String(length=100), nullable=True) #上課節次+地點
    course_student_limit: Mapped[int] = mapped_column(SmallInteger) #上限人數
    course_student_registered: Mapped[int] = mapped_column(SmallInteger) #登記人數
    course_student_selected: Mapped[int] = mapped_column(SmallInteger) #選上人數
    course_can_cross_class: Mapped[str] = mapped_column(String(length=10), nullable=True) #可跨班
    course_note: Mapped[str] = mapped_column(String(length=200), nullable=True) #備註
    course_day_night: Mapped[bool] = mapped_column(Boolean, nullable=False) #日間or夜間

    course_week_times: Mapped[list["CourseWeekTime"]] = relationship("CourseWeekTime", uselist=True, back_populates="course")


class CourseWeekTime(Base):
    __tablename__ = "course_week_times"
    week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    time: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)

    course: Mapped["Course"] = relationship("Course", uselist=False, back_populates="course_week_times")


class UserCourseMap(Base):
    __tablename__ = "user_course_maps"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)