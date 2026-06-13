from django.db import models
from django.utils import timezone


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

    lens = models.ForeignKey(Lens, on_delete=models.CASCADE, related_name='wear_records', verbose_name='镜片')
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
        return f'{self.lens.brand} - {self.wear_date} - {self.duration_hours}h'
