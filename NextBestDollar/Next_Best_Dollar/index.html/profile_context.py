"""Question visibility follows the person's current circumstances."""
def active_context(status,student_work='No'):
    working=status in ('Full-time','Part-time','Self-employed') or (status=='Student' and student_work=='Yes')
    keys=set()
    if status=='Student':keys.update(('school_name','study_program','student_work'))
    if working:keys.update(('employer_name','occupation','work_sector','retirement_access','retirement_plan_name'))
    return keys
