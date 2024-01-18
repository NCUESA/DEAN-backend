from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, SmallInteger, ForeignKey


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, unique=True, nullable=False, autoincrement=True)


class User(Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(length=20), index=True, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(length=100))


class Course(Base):
    __tablename__ = "courses"
    course_id: Mapped[str] = mapped_column(String(length=10), unique=True, index=True, nullable=False)
    course_class: Mapped[str] = mapped_column(String(length=20))
    course_name: Mapped[str] = mapped_column(String(length=500))
    course_syllabus: Mapped[str] = mapped_column(String(length=200), nullable=True)
    course_type1: Mapped[str] = mapped_column(String(length=20), nullable=True)
    course_type2: Mapped[str] = mapped_column(String(length=20), nullable=True)
    course_fully_eng: Mapped[bool] = mapped_column(Boolean)
    course_credit: Mapped[int] = mapped_column(SmallInteger)
    course_teacher: Mapped[str] = mapped_column(String(length=100))
    course_building: Mapped[str] = mapped_column(String(length=50), nullable=True)
    course_time_and_loc: Mapped[str] = mapped_column(String(length=100), nullable=True)
    course_student_limit: Mapped[int] = mapped_column(SmallInteger)
    course_student_registered: Mapped[int] = mapped_column(SmallInteger)
    course_student_selected: Mapped[int] = mapped_column(SmallInteger)
    course_note: Mapped[str] = mapped_column(String(length=50), nullable=True)


class UserCourseMap(Base):
    __tablename__ = "user_course_maps"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)