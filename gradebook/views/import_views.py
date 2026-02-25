from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from gradebook.forms import ImportUploadForm
from gradebook.models import Exam, ExamImport
from gradebook.services.import_exam import (
    DuplicateImportError,
    compute_sha256,
    import_exam_from_xlsx_bytes,
    stage_exam_import,
)
from gradebook.services.xlsx_parser import parse_exam_xlsx


@login_required
def import_upload(request):
    if request.method == "POST":
        form = ImportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data["file"]
            if upload.size > settings.UPLOAD_MAX_BYTES:
                form.add_error("file", f"文件过大，最大支持 {settings.UPLOAD_MAX_BYTES // 1024 // 1024}MB")
                return render(request, "gradebook/import_upload.html", {"form": form})

            if not upload.name.lower().endswith(".xlsx"):
                form.add_error("file", "当前仅支持 .xlsx 文件")
                return render(request, "gradebook/import_upload.html", {"form": form})

            payload = upload.read()
            source_hash = compute_sha256(payload)
            if Exam.objects.filter(source_sha256=source_hash).exists():
                form.add_error("file", "该文件已导入，请勿重复上传")
                return render(request, "gradebook/import_upload.html", {"form": form})

            parsed = parse_exam_xlsx(payload)
            preview = {
                "student_count": parsed.student_count,
                "question_count": len(parsed.question_keys),
                "excluded_from_stats_count": parsed.excluded_from_stats_count,
                "mismatched_id_count": parsed.mismatched_id_count,
                "question_keys": parsed.question_keys,
            }

            staged = ExamImport.objects.filter(source_sha256=source_hash, status=ExamImport.STATUS_STAGED).first()
            if staged:
                staged.exam_name = form.cleaned_data["exam_name"]
                staged.exam_date = form.cleaned_data["exam_date"]
                staged.source_filename = upload.name
                staged.preview_json = preview
                staged.payload = payload
                staged.save(
                    update_fields=[
                        "exam_name",
                        "exam_date",
                        "source_filename",
                        "preview_json",
                        "payload",
                    ]
                )
            else:
                staged = stage_exam_import(
                    file_bytes=payload,
                    exam_name=form.cleaned_data["exam_name"],
                    exam_date=form.cleaned_data["exam_date"],
                    source_filename=upload.name,
                    preview=preview,
                )

            return render(
                request,
                "gradebook/import_preview.html",
                {
                    "form": form,
                    "staged": staged,
                    "preview": preview,
                },
            )
    else:
        form = ImportUploadForm()

    return render(request, "gradebook/import_upload.html", {"form": form})


@login_required
def import_confirm(request, import_id: int):
    if request.method != "POST":
        return redirect("import_upload")

    staged = get_object_or_404(ExamImport, id=import_id)
    if staged.status == ExamImport.STATUS_IMPORTED:
        messages.info(request, "该导入任务已经完成")
        return redirect("exam_list")

    try:
        exam = import_exam_from_xlsx_bytes(
            file_bytes=bytes(staged.payload),
            exam_name=staged.exam_name,
            exam_date=staged.exam_date,
            source_filename=staged.source_filename,
        )
    except DuplicateImportError as exc:
        staged.status = ExamImport.STATUS_FAILED
        staged.error = str(exc)
        staged.save(update_fields=["status", "error"])
        messages.error(request, str(exc))
        return redirect("import_upload")
    except Exception as exc:  # pragma: no cover - defensive path
        staged.status = ExamImport.STATUS_FAILED
        staged.error = str(exc)
        staged.save(update_fields=["status", "error"])
        messages.error(request, "导入失败，请检查文件格式")
        return redirect("import_upload")

    staged.status = ExamImport.STATUS_IMPORTED
    staged.error = ""
    staged.save(update_fields=["status", "error"])
    messages.success(request, "导入成功")
    return redirect(reverse("exam_detail", kwargs={"exam_id": exam.id}))
