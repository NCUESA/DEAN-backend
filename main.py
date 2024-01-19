import aiohttp

import logging

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from bs4 import BeautifulSoup, ResultSet

from exceptions import UnauthenticatedException, DuplicateModelException
from dependencies import get_db
from routes import auth, course
from models import Course, CourseWeekTime

'''
async def get_day_courses():
    return requests.post("https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=D&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest")

async def get_night_courses():
    return requests.post("https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=N&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest")
'''

async def get_week_times(string: str) -> dict[int, set[int]]:
    tokens = string.split()
    week_times = {}
    current_week = None
    for token in tokens:
        if token.startswith("(") and token.endswith(")"):
            match token:
                case "(一)":
                    current_week = 1
                case "(二)":
                    current_week = 2
                case "(三)":
                    current_week = 3
                case "(四)":
                    current_week = 4
                case "(五)":
                    current_week = 5
                case "(六)":
                    current_week = 6
                case "(七)":
                    current_week = 0
                case _:
                    current_week = None
            week_times[current_week] = set()
        elif "-" in token or "、" in token:
            splited_tokens = token.split("、")
            for splited_token in splited_tokens:
                if "-" in splited_token:
                    time_range = splited_token.split("-")
                    try:
                        lower_bound = int(time_range[0])
                        upper_bound = int(time_range[1])
                    except ValueError:
                        continue
                    if lower_bound < 1 or lower_bound > 14 or upper_bound < 1 or upper_bound > 14:
                        continue
                    times = list(range(lower_bound, upper_bound+1))
                    for t in times:
                        week_times[current_week].add(t)
                else:
                    week_times[current_week].add(int(splited_token))
    return week_times

async def process(rows: ResultSet, db: Session, courses_id_map: dict, day: bool = True):
    for idx, row in enumerate(rows):
        if idx == 0:
            continue
        texts = []
        for idx, col in enumerate(row.find_all("td")):
            if idx == 4:
                texts.append("https://webap0.ncue.edu.tw" + col.find("a").get("href") if col.find("a") else "")
            elif idx == 9:
                texts.append(("|".join(col.find_all(string=True)) + "|" + col.find("a").get("href")).replace("javascript: OpenWin", "").replace("(", "").replace(")", "") if col.find("a") else "|".join(col.find_all(string=True)))
            else:
                texts.append("|".join(col.find_all(string=True)))
        processed_texts = []
        for text in texts:
            text_arr = text.split("|")
            clean_texts = [sliced_text.replace(u"\xa0", "").replace(u"\r", "").replace(u"\n", "").strip() for sliced_text in text_arr]
            processed_text = "|".join([clean_text for clean_text in clean_texts if clean_text])
            processed_texts.append(processed_text)

        if not courses_id_map.get(processed_texts[1]):
            names = processed_texts[3].split("|")
            fully_eng = True if processed_texts[7] == "是" else False
            teacher_name_link = processed_texts[9].split("|")
            course = Course(
                course_id=processed_texts[1],
                course_class=processed_texts[2],
                course_zh_name=names[0],
                course_en_name=names[1] if len(names) == 2 else "",
                course_syllabus=processed_texts[4],
                course_type1=processed_texts[5],
                course_type2=processed_texts[6],
                course_fully_eng=fully_eng,
                course_credit=int(processed_texts[8]),
                course_teacher_name=teacher_name_link[0],
                course_teacher_link=teacher_name_link[1] if len(teacher_name_link) == 2 else "",
                course_building=processed_texts[10],
                course_time_and_loc=processed_texts[11],
                course_student_limit=int(processed_texts[12]),
                course_student_registered=int(processed_texts[13]),
                course_student_selected=int(processed_texts[14]),
                course_can_cross_class=processed_texts[15],
                course_note=processed_texts[16],
                course_day_night=day
            )
            db.add(course)
            db.flush()
            week_times = await get_week_times(processed_texts[11])
            new_course_week_times = []
            for week in week_times:
                course_week_times = db.query(CourseWeekTime).filter(CourseWeekTime.course_id == course.id, CourseWeekTime.week == week).all()
                course_week_times_times = [course_week_time.time for course_week_time in course_week_times]
                for course_week_time in course_week_times:
                    if course_week_time.time not in week_times[week]:
                        course_week_time.is_disabled = True
                for t in week_times[week]:
                    if t not in course_week_times_times:
                        new_course_week_times.append(CourseWeekTime(course_id=course.id, week=week, time=t, is_disabled=False))
            db.add_all(new_course_week_times)
            db.flush()
            continue

        update_data = {}
        if processed_texts[2] != courses_id_map[processed_texts[1]]["course_class"]:
            update_data["course_class"] = processed_texts[2]
        names = processed_texts[3].split("|")
        if names[0] != courses_id_map[processed_texts[1]]["course_zh_name"]:
            update_data["course_zh_name"] = names[0]
        if len(names) == 2 and names[1] != courses_id_map[processed_texts[1]]["course_en_name"]:
            update_data["course_en_name"] = names[1]
        if processed_texts[4] != courses_id_map[processed_texts[1]]["course_syllabus"]:
            update_data["course_syllabus"] = processed_texts[4]
        if processed_texts[5] != courses_id_map[processed_texts[1]]["course_type1"]:
            update_data["course_type1"] = processed_texts[5]
        if processed_texts[6] != courses_id_map[processed_texts[1]]["course_type2"]:
            update_data["course_type2"] = processed_texts[6]
        course_fully_eng = True if processed_texts[7] == "是" else False
        if course_fully_eng != courses_id_map[processed_texts[1]]["course_fully_eng"]:
            update_data["course_fully_eng"] = course_fully_eng
        if int(processed_texts[8]) != courses_id_map[processed_texts[1]]["course_credit"]:
            update_data["course_credit"] = int(processed_texts[8])
        teacher_name_link = processed_texts[9].split("|")
        if teacher_name_link[0] != courses_id_map[processed_texts[1]]["course_teacher_name"]:
            update_data["course_teacher_name"] = teacher_name_link[0]
        if len(teacher_name_link) == 2 and teacher_name_link[1] != courses_id_map[processed_texts[1]]["course_teacher_link"]:
            update_data["course_teacher_link"] = teacher_name_link[1]
        if processed_texts[10] != courses_id_map[processed_texts[1]]["course_building"]:
            update_data["course_building"] = processed_texts[10]
        if processed_texts[11] != courses_id_map[processed_texts[1]]["course_time_and_loc"]:
            update_data["course_time_and_loc"] = processed_texts[11]
        week_times = await get_week_times(processed_texts[11])
        new_course_week_times = []
        for week in week_times:
            course_week_times = db.query(CourseWeekTime).filter(CourseWeekTime.course_id == courses_id_map[processed_texts[1]]["id"], CourseWeekTime.week == week).all()
            course_week_times_times = [course_week_time.time for course_week_time in course_week_times]
            for course_week_time in course_week_times:
                if course_week_time.time not in week_times[week]:
                    course_week_time.is_disabled = True
            for idx, time in enumerate(week_times[week]):
                if time not in course_week_times_times:
                    new_course_week_times.append(CourseWeekTime(course_id=courses_id_map[processed_texts[1]]["id"], week=week, time=time, is_disabled=False))
                elif course_week_times[idx].is_disabled:
                    course_week_times[idx].is_disabled = False
        if int(processed_texts[12]) != courses_id_map[processed_texts[1]]["course_student_limit"]:
            update_data["course_student_limit"] = int(processed_texts[12])    
        if int(processed_texts[13]) != courses_id_map[processed_texts[1]]["course_student_registered"]:
            update_data["course_student_registered"] = int(processed_texts[13]) 
        if int(processed_texts[14]) != courses_id_map[processed_texts[1]]["course_student_selected"]:
            update_data["course_student_selected"] = int(processed_texts[14])
        if processed_texts[15] != courses_id_map[processed_texts[1]]["course_can_cross_class"]:
            update_data["course_can_cross_class"] = processed_texts[15]
        if processed_texts[16] != courses_id_map[processed_texts[1]]["course_note"]:
            update_data["course_note"] = processed_texts[16]
        if day != courses_id_map[processed_texts[1]]["course_day_night"]:
            update_data["course_day_night"] = day
        if new_course_week_times:
            db.add_all(new_course_week_times)
        if update_data:
            db.query(Course).filter(Course.course_id == processed_texts[1]).update(update_data)

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job(IntervalTrigger(seconds=30))
async def request():
    print(f"Task start")
    db = await get_db().__anext__()
    courses = db.query(Course).all()
    courses_id_map = {}
    for course in courses:
        courses_id_map[course.course_id] = {
            "id": course.id,
            "course_class": course.course_class,
            "course_zh_name": course.course_zh_name,
            "course_en_name": course.course_en_name,
            "course_syllabus": course.course_syllabus,
            "course_type1": course.course_type1,
            "course_type2": course.course_type2,
            "course_fully_eng": course.course_fully_eng,
            "course_credit": course.course_credit,
            "course_teacher_name":course.course_teacher_name,
            "course_teacher_link":course.course_teacher_link,
            "course_building": course.course_building,
            "course_time_and_loc": course.course_time_and_loc,
            "course_student_limit": course.course_student_limit,
            "course_student_registered": course.course_student_registered,
            "course_student_selected": course.course_student_selected,
            "course_can_cross_class": course.course_can_cross_class,
            "course_note": course.course_note,
            "course_day_night": course.course_day_night
        }
    print("Fetching...")
    async with aiohttp.request('POST', "https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=D&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest") as day_course_response:
        day_course_rows = BeautifulSoup(await day_course_response.read(), 'html.parser').find_all("tr")
    async with aiohttp.request('POST', "https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=N&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest") as night_course_response:
        night_course_rows = BeautifulSoup(await night_course_response.read(), 'html.parser').find_all("tr")
    print("Processing...")
    await process(rows=day_course_rows, db=db, courses_id_map=courses_id_map)
    await process(rows=night_course_rows, db=db, courses_id_map=courses_id_map, day=False)
    db.flush()
    db.commit()
    print(f"Task done")

@asynccontextmanager
async def lifespan(app: FastAPI):
    server_logger = logging.getLogger()
    server_logger.setLevel(logging.INFO)
    server_file_handler = logging.FileHandler('./logs/server.log', encoding='utf8')
    server_formatter = logging.Formatter("%(asctime)s - %(module)s - %(funcName)s - line:%(lineno)d - %(levelname)s - %(message)s")
    server_file_handler.setFormatter(server_formatter)
    server_logger.addHandler(server_file_handler)
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.WARNING)
    sqlalchemy_file_handler = logging.FileHandler('./logs/sqlalchemy.log', encoding='utf8')
    sqlalchemy_formatter = logging.Formatter("%(asctime)s - %(module)s - %(funcName)s - line:%(lineno)d - %(levelname)s - %(message)s")
    sqlalchemy_file_handler.setFormatter(sqlalchemy_formatter)
    sqlalchemy_logger.addHandler(sqlalchemy_file_handler)
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_file_handler = logging.FileHandler('./logs/api.log', encoding='utf8')
    uvicorn_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    uvicorn_file_handler.setFormatter(uvicorn_formatter)
    uvicorn_logger.addHandler(uvicorn_file_handler)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(UnauthenticatedException)
async def unauthenticated(request: Request, exc: UnauthenticatedException):
    return JSONResponse(content={"message": "Not authenticated"}, status_code=401)

@app.exception_handler(DuplicateModelException)
async def duplicate(request: Request, exc: DuplicateModelException):
    return JSONResponse(content={"message": f"The {exc.attribute_name} has been used"}, status_code=409)

app.include_router(auth.router)
app.include_router(course.router)