from django.db import models
from django.db.models import Sum, Avg
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

    USAGE_FREQUENCY_CHOICES = [
        ('frequent', '常用'),
        ('occasional', '偶尔'),
        ('rare', '很少'),
    ]
    RESTOCK_PRIORITY_CHOICES = [
        ('high', '高优先级'),
        ('medium', '中优先级'),
        ('low', '低优先级'),
    ]

    purchase_channel = models.CharField('购买渠道', max_length=100, blank=True, default='')
    unit_price = models.DecimalField('单价(元)', max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField('折扣(%)', max_digits=5, decimal_places=2, default=100.00)
    shipping_fee = models.DecimalField('运费(元)', max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField('实付金额(元)', max_digits=10, decimal_places=2, default=0.00)
    stock_quantity = models.IntegerField('库存数量(片)', default=2)
    usage_frequency = models.CharField('常用程度', max_length=20, choices=USAGE_FREQUENCY_CHOICES, default='occasional')
    planned_restock_date = models.DateField('计划补货日期', null=True, blank=True)
    restock_priority = models.CharField('补货优先级', max_length=20, choices=RESTOCK_PRIORITY_CHOICES, default='medium')
    budget_month = models.CharField('预算月份', max_length=7, blank=True, default='')
    restock_notes = models.TextField('补货备注', blank=True, default='')

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

    def get_remaining_stock(self):
        used_count = self.used_count or 0
        return max(0, self.stock_quantity - used_count)

    def get_monthly_usage_rate(self):
        today = timezone.now().date()
        ninety_days_ago = today - timedelta(days=90)
        records = self.wear_records.filter(wear_date__gte=ninety_days_ago)
        total_used = records.count()
        if total_used == 0:
            return 0
        return round(total_used / 3.0, 1)

    def get_estimated_days_left(self):
        remaining = self.get_remaining_stock()
        monthly_rate = self.get_monthly_usage_rate()
        if monthly_rate <= 0:
            return None
        daily_rate = monthly_rate / 30.0
        return round(remaining / daily_rate) if daily_rate > 0 else None

    def get_total_spent(self):
        total = self.purchase_records.aggregate(Sum('actual_paid'))['actual_paid__sum'] or 0
        return float(total)

    def get_days_since_last_wear(self):
        last_record = self.wear_records.order_by('-wear_date').first()
        if not last_record:
            return (timezone.now().date() - self.created_at.date()).days
        return (timezone.now().date() - last_record.wear_date).days

    def get_restock_status(self):
        today = timezone.now().date()
        remaining = self.get_remaining_stock()
        estimated_days = self.get_estimated_days_left()
        days_until_expiry = self.days_until_expiry()

        if self.status == 'used_up':
            return {'status': 'used_up', 'label': '已用完', 'class': 'tag-gray'}

        if self.is_expired():
            return {'status': 'expired', 'label': '已过期', 'class': 'tag-red'}

        if remaining <= 0:
            return {'status': 'out_of_stock', 'label': '已无库存', 'class': 'tag-red'}

        if estimated_days is not None and estimated_days <= 7:
            return {'status': 'urgent', 'label': f'库存紧急(剩{estimated_days}天)', 'class': 'tag-red'}

        if remaining <= 2:
            return {'status': 'low', 'label': f'库存不足(剩{remaining}片)', 'class': 'tag-yellow'}

        if days_until_expiry <= 30 and remaining > 0:
            return {'status': 'expiring_with_stock', 'label': f'临期有库存(剩{days_until_expiry}天)', 'class': 'tag-yellow'}

        if self.planned_restock_date and (self.planned_restock_date - today).days <= 7:
            return {'status': 'planned_soon', 'label': '计划补货中', 'class': 'tag-blue'}

        return {'status': 'normal', 'label': f'库存充足(剩{remaining}片)', 'class': 'tag-green'}

    def get_avg_comfort_level(self):
        avg = self.wear_records.aggregate(Avg('comfort_level'))['comfort_level__avg']
        return round(avg, 1) if avg else None

    def is_low_comfort_high_cost(self):
        avg_comfort = self.get_avg_comfort_level()
        total_spent = self.get_total_spent()
        if avg_comfort is None:
            return False
        return avg_comfort <= 2 and total_spent > 0

    def get_cost_per_wear(self):
        total_spent = self.get_total_spent()
        total_wears = self.wear_records.count()
        if total_wears == 0 or total_spent == 0:
            return None
        return round(total_spent / total_wears, 2)


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


class OutfitPlan(models.Model):
    SCENE_CHOICES = [
        ('daily', '日常通勤'),
        ('date', '约会'),
        ('party', '派对/聚会'),
        ('wedding', '婚礼/宴会'),
        ('photo', '拍照/写真'),
        ('travel', '旅行/出游'),
        ('interview', '面试/商务'),
        ('sports', '运动'),
        ('other', '其他'),
    ]

    MAKEUP_STYLE_CHOICES = [
        ('natural', '自然裸妆'),
        ('fresh', '清新淡妆'),
        ('elegant', '优雅知性'),
        ('sweet', '甜美可爱'),
        ('sexy', '性感妩媚'),
        ('cool', '酷飒欧美'),
        ('gothic', '哥特暗黑'),
        ('korean', '韩系妆容'),
        ('japanese', '日系妆容'),
        ('custom', '自定义风格'),
    ]

    CLOTHING_COLOR_CHOICES = [
        ('warm', '暖色系'),
        ('cool', '冷色系'),
        ('neutral', '中性色系'),
        ('earth', '大地色系'),
        ('pastel', '马卡龙色系'),
        ('monochrome', '黑白灰'),
        ('bright', '鲜艳亮色'),
        ('mixed', '撞色搭配'),
    ]

    LIGHTING_CHOICES = [
        ('natural_day', '自然光(白天)'),
        ('natural_sunset', '自然光(黄昏)'),
        ('indoor_soft', '室内柔光'),
        ('indoor_bright', '室内强光'),
        ('neon', '霓虹灯光'),
        ('candle', '烛光/暖光'),
        ('flash', '闪光灯'),
        ('mixed', '混合光线'),
    ]

    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('completed', '已执行'),
        ('cancelled', '已取消'),
    ]

    TAG_CHOICES = [
        ('high_look_low_comfort', '高颜值但低舒适'),
        ('comfort_low_fit', '舒适但不适配场景'),
        ('reusable', '适合重复使用'),
        ('perfect_match', '完美搭配'),
        ('needs_adjustment', '需要调整'),
        ('overtime', '佩戴超时'),
        ('undertime', '佩戴不足'),
    ]

    lens = models.ForeignKey(Lens, on_delete=models.SET_NULL, null=True, blank=True, related_name='outfit_plans', verbose_name='推荐镜片')
    backup_lens = models.ForeignKey(Lens, on_delete=models.SET_NULL, null=True, blank=True, related_name='backup_outfit_plans', verbose_name='备选镜片')
    scene_name = models.CharField('场景名称', max_length=50, choices=SCENE_CHOICES, default='daily')
    custom_scene_name = models.CharField('自定义场景', max_length=100, blank=True, default='')
    makeup_style = models.CharField('妆容风格', max_length=30, choices=MAKEUP_STYLE_CHOICES, default='natural')
    custom_makeup_style = models.CharField('自定义妆容风格', max_length=100, blank=True, default='')
    clothing_color = models.CharField('服饰色系', max_length=30, choices=CLOTHING_COLOR_CHOICES, default='neutral')
    lighting = models.CharField('光线环境', max_length=30, choices=LIGHTING_CHOICES, default='natural_day')
    expected_wear_date = models.DateField('预计佩戴日期')
    expected_duration_hours = models.FloatField('预计佩戴时长(小时)', default=8.0)
    match_score = models.IntegerField('搭配评分(1-5)', default=4)
    notes = models.TextField('备注', blank=True, default='')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    tags = models.JSONField('标签', default=list, blank=True)
    wear_record = models.OneToOneField(WearRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='outfit_plan', verbose_name='关联佩戴记录')
    executed_at = models.DateTimeField('执行时间', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'outfit_plan'
        ordering = ['-expected_wear_date', '-created_at']
        verbose_name = '妆容搭配计划'
        verbose_name_plural = verbose_name

    def __str__(self):
        scene = self.custom_scene_name or self.get_scene_name_display()
        return f'{scene} - {self.expected_wear_date}'

    def get_scene_display_name(self):
        return self.custom_scene_name or self.get_scene_name_display()

    def get_makeup_display_name(self):
        return self.custom_makeup_style or self.get_makeup_style_display()

    def generate_tags(self):
        if not self.wear_record:
            return []

        tags = []
        record = self.wear_record

        if self.match_score >= 4 and record.comfort_level <= 2:
            tags.append('high_look_low_comfort')

        if self.match_score <= 2 and record.comfort_level >= 4:
            tags.append('comfort_low_fit')

        if self.match_score >= 4 and record.comfort_level >= 4:
            tags.append('perfect_match')

        if self.match_score >= 4 and record.comfort_level >= 4 and abs(record.duration_hours - self.expected_duration_hours) <= 1:
            tags.append('reusable')

        if self.match_score <= 2 or record.comfort_level <= 2:
            tags.append('needs_adjustment')

        if record.duration_hours > self.expected_duration_hours + 1:
            tags.append('overtime')

        if record.duration_hours < self.expected_duration_hours - 1:
            tags.append('undertime')

        return tags

    def update_tags(self):
        self.tags = self.generate_tags()
        return self.tags

    def mark_as_completed(self, wear_record=None):
        self.status = 'completed'
        self.executed_at = timezone.now()
        if wear_record:
            self.wear_record = wear_record
            self.update_tags()
        self.save()

    def get_duration_diff(self):
        if not self.wear_record:
            return None
        return round(self.wear_record.duration_hours - self.expected_duration_hours, 1)

    def get_comfort_diff(self):
        if not self.wear_record:
            return None
        return self.wear_record.comfort_level - self.match_score


class PurchaseRecord(models.Model):
    CHANNEL_CHOICES = [
        ('taobao', '淘宝'),
        ('tmall', '天猫'),
        ('jd', '京东'),
        ('pdd', '拼多多'),
        ('xiaohongshu', '小红书'),
        ('offline', '线下实体店'),
        ('other', '其他渠道'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', '待付款'),
        ('paid', '已付款'),
        ('refunded', '已退款'),
    ]

    lens = models.ForeignKey(Lens, on_delete=models.CASCADE, related_name='purchase_records', verbose_name='关联镜片')
    purchase_date = models.DateField('采购日期')
    purchase_channel = models.CharField('购买渠道', max_length=50, choices=CHANNEL_CHOICES, default='taobao')
    custom_channel = models.CharField('自定义渠道', max_length=100, blank=True, default='')
    quantity = models.IntegerField('采购数量(片)', default=2)
    unit_price = models.DecimalField('单价(元)', max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField('折扣(%)', max_digits=5, decimal_places=2, default=100.00)
    shipping_fee = models.DecimalField('运费(元)', max_digits=10, decimal_places=2, default=0.00)
    coupon_amount = models.DecimalField('优惠券金额(元)', max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField('商品总额(元)', max_digits=10, decimal_places=2, default=0.00)
    actual_paid = models.DecimalField('实付金额(元)', max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField('付款状态', max_length=20, choices=PAYMENT_STATUS_CHOICES, default='paid')
    order_number = models.CharField('订单号', max_length=100, blank=True, default='')
    budget_month = models.CharField('预算月份', max_length=7, blank=True, default='')
    notes = models.TextField('备注', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'purchase_record'
        ordering = ['-purchase_date', '-created_at']
        verbose_name = '采购记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.lens.brand if self.lens else "Unknown"} - {self.get_purchase_channel_display()} - {self.purchase_date}'

    def get_channel_display_name(self):
        return self.custom_channel or self.get_purchase_channel_display()

    def calculate_total(self):
        discount_multiplier = float(self.discount) / 100.0 if self.discount else 1.0
        self.total_amount = float(self.unit_price) * int(self.quantity) * discount_multiplier
        self.actual_paid = self.total_amount + float(self.shipping_fee) - float(self.coupon_amount)
        return self.actual_paid

    def save(self, *args, **kwargs):
        if not self.budget_month and self.purchase_date:
            self.budget_month = self.purchase_date.strftime('%Y-%m')
        self.calculate_total()
        super().save(*args, **kwargs)


class RestockSuggestion(models.Model):
    SUGGESTION_TYPE_CHOICES = [
        ('low_stock', '库存不足'),
        ('expiring_soon', '即将过期'),
        ('high_usage', '高频使用'),
        ('long_unused', '长期未用'),
        ('low_comfort', '低舒适度'),
        ('planned', '计划补货'),
        ('seasonal', '季节性补货'),
    ]

    SEVERITY_CHOICES = [
        ('critical', '紧急'),
        ('important', '重要'),
        ('normal', '常规'),
    ]

    lens = models.ForeignKey(Lens, on_delete=models.CASCADE, related_name='restock_suggestions', verbose_name='关联镜片')
    suggestion_type = models.CharField('建议类型', max_length=30, choices=SUGGESTION_TYPE_CHOICES)
    severity = models.CharField('严重程度', max_length=20, choices=SEVERITY_CHOICES, default='normal')
    title = models.CharField('标题', max_length=200)
    message = models.TextField('建议内容')
    current_stock = models.IntegerField('当前库存', default=0)
    estimated_days_left = models.IntegerField('预计可用天数', null=True, blank=True)
    suggested_quantity = models.IntegerField('建议补货数量', default=2)
    suggested_date = models.DateField('建议补货日期', null=True, blank=True)
    is_action_taken = models.BooleanField('是否已处理', default=False)
    is_dismissed = models.BooleanField('是否已忽略', default=False)
    triggered_at = models.DateTimeField('触发时间', auto_now_add=True)
    action_taken_at = models.DateTimeField('处理时间', null=True, blank=True)
    action_notes = models.TextField('处理备注', blank=True, default='')

    class Meta:
        db_table = 'restock_suggestion'
        ordering = ['-severity', '-triggered_at']
        verbose_name = '补货建议'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'[{self.get_severity_display()}] {self.title}'
