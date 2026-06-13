from django.db import models
from django.utils import timezone
from datetime import timedelta


class Lens(models.Model):
    PURPOSE_CHOICES = [
        ('daily', '日常'),
        ('date', '约会'),
        ('photo', '拍照'),
    ]

    STATUS_CHOICES = [
        ('unopened', '未开封'),
        ('opened', '已开封'),
        ('used_up', '已用完'),
        ('expired', '已过期'),
    ]

    CARE_METHOD_CHOICES = [
        ('hydrogen_peroxide', '双氧水护理'),
        ('multi_purpose', '多功能护理液'),
        ('daily_disposable', '日抛无需护理'),
        ('other', '其他方式'),
    ]

    REPLACEMENT_CYCLE_CHOICES = [
        (1, '每天更换'),
        (7, '每周更换'),
        (14, '每2周更换'),
        (30, '每月更换'),
        (60, '每2月更换'),
        (90, '每季度更换'),
        (180, '每半年更换'),
        (365, '每年更换'),
    ]

    brand = models.CharField('品牌', max_length=100)
    model_name = models.CharField('系列/型号', max_length=100, blank=True, default='')
    color = models.CharField('颜色', max_length=50, blank=True, default='')
    power_sph = models.FloatField('球镜度数(SPH)', default=0.0)
    power_cyl = models.FloatField('柱镜度数(CYL)', default=0.0, blank=True)
    water_content = models.FloatField('含水量(%)', default=38.0)
    base_curve = models.FloatField('基弧(mm)', default=8.6)
    diameter = models.FloatField('直径(mm)', default=14.0, blank=True)
    purchase_date = models.DateField('购买日期')
    expiry_date = models.DateField('有效期至')
    open_date = models.DateField('开封日期', null=True, blank=True)
    purpose = models.CharField('用途', max_length=20, choices=PURPOSE_CHOICES, default='daily')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='unopened')
    pair_count = models.IntegerField('总片数', default=2)
    used_count = models.IntegerField('已用片数', default=0)
    notes = models.TextField('备注', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    care_solution_brand = models.CharField('护理液品牌', max_length=100, blank=True, default='')
    care_method = models.CharField(
        '护理方式', max_length=30, choices=CARE_METHOD_CHOICES,
        blank=True, default='', null=True
    )
    replacement_days_after_open = models.IntegerField(
        '开封后建议更换周期(天)', choices=REPLACEMENT_CYCLE_CHOICES,
        null=True, blank=True
    )
    next_care_date = models.DateField('下次护理日期', null=True, blank=True)
    next_checkup_date = models.DateField('下次眼科复查日期', null=True, blank=True)
    need_rest_observation = models.BooleanField('是否需要停戴观察', default=False)
    rest_until_date = models.DateField('停戴至日期', null=True, blank=True)

    class Meta:
        db_table = 'lens'
        ordering = ['-created_at']
        verbose_name = '彩瞳镜片'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.brand} {self.model_name} - {self.power_sph}D'

    def is_expired(self):
        return timezone.now().date() > self.expiry_date

    def days_until_expiry(self):
        return (self.expiry_date - timezone.now().date()).days

    def daily_wear_limit(self):
        if self.water_content >= 58:
            return 6
        elif self.water_content >= 42:
            return 8
        else:
            return 10

    def days_since_open(self):
        if not self.open_date:
            return None
        return (timezone.now().date() - self.open_date).days

    def days_until_next_care(self):
        if not self.next_care_date:
            return None
        return (self.next_care_date - timezone.now().date()).days

    def days_until_next_checkup(self):
        if not self.next_checkup_date:
            return None
        return (self.next_checkup_date - timezone.now().date()).days

    def days_until_replacement(self):
        if not self.open_date or not self.replacement_days_after_open:
            return None
        planned_end = self.open_date + timedelta(days=self.replacement_days_after_open)
        return (planned_end - timezone.now().date()).days

    def is_under_rest(self):
        if not self.need_rest_observation:
            return False
        if self.rest_until_date and timezone.now().date() <= self.rest_until_date:
            return True
        if self.rest_until_date is None:
            return True
        return False

    def get_care_status(self):
        today = timezone.now().date()
        if self.is_under_rest():
            return 'rest'
        days_care = self.days_until_next_care()
        days_checkup = self.days_until_next_checkup()
        days_replacement = self.days_until_replacement()
        if days_replacement is not None and days_replacement < 0:
            return 'replace_overdue'
        if days_care is not None and days_care < 0:
            return 'care_overdue'
        if days_checkup is not None and days_checkup < 0:
            return 'checkup_overdue'
        if days_replacement is not None and days_replacement <= 3:
            return 'replace_soon'
        if days_care is not None and days_care <= 3:
            return 'care_soon'
        if days_checkup is not None and days_checkup <= 7:
            return 'checkup_soon'
        return 'normal'


class WearRecord(models.Model):
    EYE_REACTION_CHOICES = [
        ('none', '无不适'),
        ('dryness', '干涩'),
        ('redness', '红血丝'),
        ('fatigue', '视疲劳'),
        ('dryness_redness', '干涩+红血丝'),
        ('dryness_fatigue', '干涩+视疲劳'),
        ('redness_fatigue', '红血丝+视疲劳'),
        ('all', '全部不适'),
    ]

    lens = models.ForeignKey(Lens, on_delete=models.SET_NULL, null=True, related_name='wear_records', verbose_name='镜片')
    wear_date = models.DateField('佩戴日期')
    duration_hours = models.FloatField('佩戴时长(小时)')
    comfort_level = models.IntegerField('舒适度(1-5)', default=3)
    eye_reaction = models.CharField('眼部反应', max_length=30, choices=EYE_REACTION_CHOICES, default='none')
    notes = models.TextField('备注', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wear_record'
        ordering = ['-wear_date', '-created_at']
        verbose_name = '佩戴记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.lens.brand if self.lens else "Unknown"} - {self.wear_date} - {self.duration_hours}h'


class CareRecord(models.Model):
    CARE_TYPE_CHOICES = [
        ('routine', '常规护理'),
        ('deep_clean', '深度清洁'),
        ('case_replace', '更换镜盒'),
        ('solution_replace', '更换护理液'),
        ('replacement', '镜片更换'),
        ('checkup', '眼科复查'),
        ('rest_start', '开始停戴观察'),
        ('rest_end', '结束停戴观察'),
        ('other', '其他'),
    ]

    lens = models.ForeignKey(Lens, on_delete=models.CASCADE, related_name='care_records', verbose_name='镜片')
    care_type = models.CharField('护理类型', max_length=30, choices=CARE_TYPE_CHOICES)
    care_date = models.DateField('护理/复查日期')
    notes = models.TextField('备注', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'care_record'
        ordering = ['-care_date', '-created_at']
        verbose_name = '护理记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.lens.brand} - {self.get_care_type_display()} - {self.care_date}'


class CareReminder(models.Model):
    REMINDER_TYPE_CHOICES = [
        ('care', '护理提醒'),
        ('replacement', '更换提醒'),
        ('checkup', '复查提醒'),
        ('rest', '停戴提醒'),
        ('risk', '高风险提醒'),
    ]

    SEVERITY_CHOICES = [
        ('info', '提示'),
        ('warning', '警告'),
        ('danger', '危险'),
    ]

    lens = models.ForeignKey(Lens, on_delete=models.CASCADE, related_name='reminders', verbose_name='镜片')
    reminder_type = models.CharField('提醒类型', max_length=30, choices=REMINDER_TYPE_CHOICES)
    severity = models.CharField('严重程度', max_length=20, choices=SEVERITY_CHOICES, default='info')
    title = models.CharField('标题', max_length=200)
    message = models.TextField('提醒内容')
    target_date = models.DateField('目标日期', null=True, blank=True)
    is_read = models.BooleanField('是否已读', default=False)
    is_dismissed = models.BooleanField('是否已忽略', default=False)
    triggered_by_record = models.ForeignKey(
        WearRecord, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='triggered_reminders', verbose_name='触发记录'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'care_reminder'
        ordering = ['-created_at']
        verbose_name = '护理提醒'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'[{self.get_severity_display()}] {self.title}'
