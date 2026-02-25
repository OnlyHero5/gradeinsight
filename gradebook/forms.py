from __future__ import annotations

from decimal import Decimal

from django import forms


class ImportUploadForm(forms.Form):
    exam_name = forms.CharField(max_length=255, label="考试名称")
    exam_date = forms.DateField(required=False, label="考试日期")
    file = forms.FileField(label="Excel 文件")


class QuestionFilterForm(forms.Form):
    OP_CHOICES = [
        ("eq", "等于"),
        ("ne", "不等于"),
        ("lt", "小于"),
        ("lte", "小于等于"),
        ("gt", "大于"),
        ("gte", "大于等于"),
        ("between", "区间"),
        ("below_mean", "低于本题平均分"),
        ("above_mean", "高于本题平均分"),
    ]

    question_key = forms.ChoiceField(label="题号")
    op = forms.ChoiceField(choices=OP_CHOICES, label="条件")
    value = forms.DecimalField(required=False, label="分值")
    min = forms.DecimalField(required=False, label="最小值")
    max = forms.DecimalField(required=False, label="最大值")
    include_excluded = forms.BooleanField(required=False, label="包含未扫/缺考")

    def __init__(self, *args, question_keys: list[str] | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        key_options = [(item, item) for item in (question_keys or [])]
        self.fields["question_key"].choices = key_options

    def clean(self) -> dict:
        data = super().clean()
        op = data.get("op")
        value = data.get("value")
        min_value = data.get("min")
        max_value = data.get("max")

        if op in {"eq", "ne", "lt", "lte", "gt", "gte"} and value is None:
            self.add_error("value", "当前条件需要填写分值")

        if op == "between":
            if min_value is None or max_value is None:
                self.add_error("min", "区间条件必须填写最小值与最大值")
            elif Decimal(min_value) > Decimal(max_value):
                self.add_error("max", "最大值必须大于或等于最小值")
        return data
