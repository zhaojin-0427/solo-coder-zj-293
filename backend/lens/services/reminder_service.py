from django.utils import timezone
from datetime import timedelta

from .exceptions import safe_service_call
from ..models import WearRecord, CareReminder


@safe_service_call(default_value=[], service_name="ReminderService")
def generate_reminders_from_record(record):
    """
    根据佩戴记录生成护理提醒。
    从views.py中拆分出来的提醒生成逻辑。
    """
    if not record.lens:
        return []

    lens = record.lens
    today = record.wear_date
    reminders = []

    today_records = WearRecord.objects.filter(lens=lens, wear_date=today)
    total_hours_today = sum(r.duration_hours for r in today_records)

    lens_daily_limit = lens.daily_wear_limit()
    if total_hours_today >= 12:
        reminders.append({
            'lens': lens,
            'reminder_type': 'risk',
            'severity': 'danger',
            'title': '单日佩戴严重超时',
            'message': f'今日已佩戴 {total_hours_today:.1f} 小时，远超建议上限（{lens_daily_limit}h）。建议立即取下镜片，让眼睛充分休息，至少间隔24小时再佩戴。',
            'target_date': today,
            'triggered_by_record': record,
        })
    elif total_hours_today >= lens_daily_limit + 2:
        reminders.append({
            'lens': lens,
            'reminder_type': 'risk',
            'severity': 'warning',
            'title': '单日佩戴时长偏长',
            'message': f'今日已佩戴 {total_hours_today:.1f} 小时，超过建议上限（{lens_daily_limit}h）。建议取下镜片休息，明日减少佩戴时长。',
            'target_date': today,
            'triggered_by_record': record,
        })

    if record.comfort_level <= 2:
        reminders.append({
            'lens': lens,
            'reminder_type': 'risk',
            'severity': 'warning',
            'title': '舒适度偏低',
            'message': f'本次佩戴舒适度仅 {record.comfort_level} 分（满分5分）。建议检查镜片是否有破损、沉淀物，或考虑更换护理液/镜片品牌。如持续不适请停戴并就医。',
            'target_date': today,
            'triggered_by_record': record,
        })

    if record.comfort_level <= 1:
        reminders.append({
            'lens': lens,
            'reminder_type': 'rest',
            'severity': 'danger',
            'title': '强烈建议停戴观察',
            'message': '舒适度极低，建议立即停戴此镜片至少3天。如停戴后仍有不适，请及时前往眼科就诊。',
            'target_date': today + timedelta(days=3),
            'triggered_by_record': record,
        })

    bad_reactions = ['redness', 'dryness_redness', 'redness_fatigue', 'all']
    if record.eye_reaction in bad_reactions:
        reminders.append({
            'lens': lens,
            'reminder_type': 'rest',
            'severity': 'danger',
            'title': '眼部出现充血，建议停戴',
            'message': '本次佩戴出现眼部红血丝反应，建议停戴此镜片至少2天。可使用人工泪液缓解，如症状未消退请及时就医。',
            'target_date': today + timedelta(days=2),
            'triggered_by_record': record,
        })

    moderate_reactions = ['dryness', 'fatigue', 'dryness_fatigue']
    if record.eye_reaction in moderate_reactions:
        reminders.append({
            'lens': lens,
            'reminder_type': 'care',
            'severity': 'warning',
            'title': '眼部有轻度不适',
            'message': '本次佩戴出现干涩/视疲劳，建议加强镜片护理，可考虑深度清洁或更换护理液。明日减少佩戴时长。',
            'target_date': today,
            'triggered_by_record': record,
        })

    if lens.open_date:
        days_open = (today - lens.open_date).days
        if lens.replacement_days_after_open and days_open >= lens.replacement_days_after_open:
            reminders.append({
                'lens': lens,
                'reminder_type': 'replacement',
                'severity': 'danger',
                'title': '镜片已超过建议更换周期',
                'message': f'此镜片已开封 {days_open} 天，超过建议更换周期（{lens.replacement_days_after_open}天）。为了眼部健康，请立即更换新镜片。',
                'target_date': lens.open_date + timedelta(days=lens.replacement_days_after_open),
                'triggered_by_record': record,
            })
        elif lens.replacement_days_after_open and days_open >= lens.replacement_days_after_open - 3:
            reminders.append({
                'lens': lens,
                'reminder_type': 'replacement',
                'severity': 'warning',
                'title': '镜片即将达到更换周期',
                'message': f'此镜片已开封 {days_open} 天，距离建议更换周期（{lens.replacement_days_after_open}天）仅剩 {lens.replacement_days_after_open - days_open} 天，请提前准备新镜片。',
                'target_date': lens.open_date + timedelta(days=lens.replacement_days_after_open),
                'triggered_by_record': record,
            })

    if lens.next_care_date and today >= lens.next_care_date:
        reminders.append({
            'lens': lens,
            'reminder_type': 'care',
            'severity': 'warning',
            'title': '请及时护理镜片',
            'message': f'已到达计划护理日期（{lens.next_care_date.isoformat()}），请对镜片进行清洁护理，并更新下次护理日期。',
            'target_date': lens.next_care_date,
            'triggered_by_record': record,
        })

    if lens.next_checkup_date and today >= lens.next_checkup_date:
        reminders.append({
            'lens': lens,
            'reminder_type': 'checkup',
            'severity': 'warning',
            'title': '请及时进行眼科复查',
            'message': f'已到达计划复查日期（{lens.next_checkup_date.isoformat()}），请预约眼科医生进行眼部健康检查。',
            'target_date': lens.next_checkup_date,
            'triggered_by_record': record,
        })

    created_reminders = []
    for rem_data in reminders:
        exists = CareReminder.objects.filter(
            lens=rem_data['lens'],
            reminder_type=rem_data['reminder_type'],
            title=rem_data['title'],
            created_at__date=today
        ).exists()
        if not exists:
            reminder = CareReminder.objects.create(**rem_data)
            created_reminders.append(reminder)

    return created_reminders
