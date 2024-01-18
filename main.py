import aiohttp

import logging

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from bs4 import BeautifulSoup

from exceptions import UnauthenticatedException, DuplicateModelException
from dependencies import get_db
from routes import auth
from models import Course

'''
async def get_day_courses():
    return requests.post("https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=D&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest")

async def get_night_courses():
    return requests.post("https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=N&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest")
'''

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job(IntervalTrigger(minutes=10))
async def request():
    print(f"Task start")
    db = await get_db().__anext__()
    courses = db.query(Course).all()
    courses_id_map = {}
    for course in courses:
        courses_id_map[course.course_id] = {
            "course": course,
            "course_class": course.course_class,
            "course_name": course.course_name,
            "course_syllabus": course.course_syllabus,
            "course_type1": course.course_type1,
            "course_type2": course.course_type2,
            "course_fully_eng": course.course_fully_eng,
            "course_credit": course.course_credit,
            "course_teacher":course.course_teacher,
            "course_building": course.course_building,
            "course_time_and_loc": course.course_time_and_loc,
            "course_student_limit": course.course_student_limit,
            "course_student_registered": course.course_student_registered,
            "course_student_selected": course.course_student_selected,
            "course_note": course.course_note
        }
    print("Fetching...")
    async with aiohttp.request('POST', "https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=D&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest") as day_course_response:
        day_course_rows = BeautifulSoup(await day_course_response.read(), 'html.parser').find_all("tr")
    async with aiohttp.request('POST', "https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=N&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest") as night_course_response:
        night_course_rows = BeautifulSoup(await night_course_response.read(), 'html.parser').find_all("tr")
    #day_course_response = requests.post("https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=D&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest")
    #night_course_response = requests.post("https://webap0.ncue.edu.tw/DEANV2/Other/OB010", headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, data="sel_cls_branch=N&sel_cls_branch=&sel_scr_english=&sel_scr_english=&sel_SCR_IS_DIS_LEARN=&sel_SCR_IS_DIS_LEARN=&sel_yms_year=112&sel_yms_year=112&sel_yms_smester=2&sel_yms_smester=2&scr_selcode=&sel_cls_id=&sel_cls_id=&sel_sct_week=&sel_sct_week=&sub_name=&emp_name=&X-Requested-With=XMLHttpRequest")
    print("Parsing...")
    #day_course_rows = BeautifulSoup(day_course_response.read(), 'html.parser').find_all("tr")
    #night_course_rows = BeautifulSoup(night_course_response.read(), 'html.parser').find_all("tr")
    objs = []
    print("Comparing...")
    for idx, row in enumerate(day_course_rows):
        if idx > 0:
            cols = row.find_all("td")
            texts = []
            for col in cols:
                texts.append(col.get_text())
            if not courses_id_map.get(texts[1]):
                course = Course(
                    course_id=texts[1],
                    course_class=texts[2],
                    course_name=texts[3],
                    course_syllabus=texts[4],
                    course_type1=texts[5],
                    course_type2=texts[6],
                    course_fully_eng=(True if texts[7] == "是" else False),
                    course_credit=texts[8],
                    course_teacher=texts[9],
                    course_building=texts[10],
                    course_time_and_loc=texts[11],
                    course_student_limit=texts[12],
                    course_student_registered=texts[13],
                    course_student_selected=texts[14],
                    course_note=texts[15]
                )
                objs.append(course)
            else:
                update_dict = {}
                if texts[2] != courses_id_map[texts[1]]["course_class"]:
                    update_dict["course_class"] = texts[2]
                if texts[3] != courses_id_map[texts[1]]["course_name"]:
                    update_dict["course_name"] = texts[3]
                if texts[4] != courses_id_map[texts[1]]["course_syllabus"]:
                    update_dict["course_syllabus"] = texts[4]
                if texts[5] != courses_id_map[texts[1]]["course_type1"]:
                    update_dict["course_type1"] = texts[5]
                if texts[6] != courses_id_map[texts[1]]["course_type2"]:
                    update_dict["course_type2"] = texts[6]
                texts[7] = True if texts[7] == "是" else False
                if texts[7] != courses_id_map[texts[1]]["course_fully_eng"]:
                    update_dict["course_fully_eng"] = texts[7]
                if int(texts[8]) != courses_id_map[texts[1]]["course_credit"]:
                    update_dict["course_credit"] = texts[8]
                if texts[9] != courses_id_map[texts[1]]["course_teacher"]:
                    update_dict["course_teacher"] = texts[9]
                if texts[10] != courses_id_map[texts[1]]["course_building"]:
                    update_dict["course_building"] = texts[10]
                if texts[11] != courses_id_map[texts[1]]["course_time_and_loc"]:
                    update_dict["course_time_and_loc"] = texts[11]
                if int(texts[12]) != courses_id_map[texts[1]]["course_student_limit"]:
                    update_dict["course_student_limit"] = texts[12]
                if int(texts[13]) != courses_id_map[texts[1]]["course_student_registered"]:
                    update_dict["course_student_registered"] = texts[13]
                if int(texts[14]) != courses_id_map[texts[1]]["course_student_selected"]:
                    update_dict["course_student_selected"] = texts[14]
                if texts[15] != courses_id_map[texts[1]]["course_note"]:
                    update_dict["course_note"] = texts[15]
                if update_dict:
                    db.query(Course).filter(Course.course_id == texts[1]).update(update_dict)
    for idx, row in enumerate(night_course_rows):
        if idx > 0:
            cols = row.find_all("td")
            texts = []
            for col in cols:
                texts.append(col.get_text())
            if not courses_id_map.get(texts[1]):
                course = Course(
                    course_id=texts[1],
                    course_class=texts[2],
                    course_name=texts[3],
                    course_syllabus=texts[4],
                    course_type1=texts[5],
                    course_type2=texts[6],
                    course_fully_eng=(True if texts[7] == "是" else False),
                    course_credit=texts[8],
                    course_teacher=texts[9],
                    course_building=texts[10],
                    course_time_and_loc=texts[11],
                    course_student_limit=texts[12],
                    course_student_registered=texts[13],
                    course_student_selected=texts[14],
                    course_note=texts[15]
                )
                objs.append(course)
            else:
                update_dict = {}
                if texts[2] != courses_id_map[texts[1]]["course_class"]:
                    update_dict["course_class"] = texts[2]
                if texts[3] != courses_id_map[texts[1]]["course_name"]:
                    update_dict["course_name"] = texts[3]
                if texts[4] != courses_id_map[texts[1]]["course_syllabus"]:
                    update_dict["course_syllabus"] = texts[4]
                if texts[5] != courses_id_map[texts[1]]["course_type1"]:
                    update_dict["course_type1"] = texts[5]
                if texts[6] != courses_id_map[texts[1]]["course_type2"]:
                    update_dict["course_type2"] = texts[6]
                texts[7] = True if texts[7] == "是" else False
                if texts[7] != courses_id_map[texts[1]]["course_fully_eng"]:
                    update_dict["course_fully_eng"] = texts[7]
                if int(texts[8]) != courses_id_map[texts[1]]["course_credit"]:
                    update_dict["course_credit"] = texts[8]
                if texts[9] != courses_id_map[texts[1]]["course_teacher"]:
                    update_dict["course_teacher"] = texts[9]
                if texts[10] != courses_id_map[texts[1]]["course_building"]:
                    update_dict["course_building"] = texts[10]
                if texts[11] != courses_id_map[texts[1]]["course_time_and_loc"]:
                    update_dict["course_time_and_loc"] = texts[11]
                if int(texts[12]) != courses_id_map[texts[1]]["course_student_limit"]:
                    update_dict["course_student_limit"] = texts[12]
                if int(texts[13]) != courses_id_map[texts[1]]["course_student_registered"]:
                    update_dict["course_student_registered"] = texts[13]
                if int(texts[14]) != courses_id_map[texts[1]]["course_student_selected"]:
                    update_dict["course_student_selected"] = texts[14]
                if texts[15] != courses_id_map[texts[1]]["course_note"]:
                    update_dict["course_note"] = texts[15]
                if update_dict:
                    db.query(Course).filter(Course.course_id == texts[1]).update(update_dict)
    print("Database processing...")
    db.add_all(objs)
    db.flush()
    db.commit()
    print(f"Task done")

@asynccontextmanager
async def lifespan(app: FastAPI):
    server_logger = logging.getLogger()
    server_logger.setLevel(logging.INFO)
    server_file_handler = logging.FileHandler('./logs/server.log')
    server_formatter = logging.Formatter("%(asctime)s - %(module)s - %(funcName)s - line:%(lineno)d - %(levelname)s - %(message)s")
    server_file_handler.setFormatter(server_formatter)
    server_logger.addHandler(server_file_handler)
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_file_handler = logging.FileHandler('./logs/api.log')
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