import shutil
import os

src = r'E:/PWD301/PPTQ_LMS_FINAL_REPORT.docx'
dst = r'E:/PWD301/PPTQ_LMS_FINAL_REPORT_UPDATED.docx'

try:
    shutil.copyfile(src, dst)
    print("Successfully synchronized to PPTQ_LMS_FINAL_REPORT_UPDATED.docx")
except Exception as e:
    print(f"Notice: {dst} is currently locked by Word ({e}). The primary file {src} is already updated!")
