'''
    for idx, row in enumerate(day_course_rows):
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
                course_note=processed_texts[16]
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
                for time in week_times[week]:
                    if time not in course_week_times_times:
                        new_course_week_times.append(CourseWeekTime(course_id=course.id, week=week, time=time, is_disabled=False))
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
        update_data["course_teacher_name"] = teacher_name_link[0]
        if len(teacher_name_link) == 2:
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
            for time in week_times[week]:
                if time not in course_week_times_times:
                    new_course_week_times.append(CourseWeekTime(course_id=courses_id_map[processed_texts[1]]["id"], week=week, time=time, is_disabled=False))
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
        if new_course_week_times:
            db.add_all(new_course_week_times)
        if update_data:
            db.query(Course).filter(Course.course_id == processed_texts[1]).update(update_data)
    '''