from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Lens',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand', models.CharField(max_length=100, verbose_name='品牌')),
                ('model_name', models.CharField(blank=True, default='', max_length=100, verbose_name='系列/型号')),
                ('color', models.CharField(blank=True, default='', max_length=50, verbose_name='颜色')),
                ('power_sph', models.FloatField(default=0.0, verbose_name='球镜度数(SPH)')),
                ('power_cyl', models.FloatField(blank=True, default=0.0, verbose_name='柱镜度数(CYL)')),
                ('water_content', models.FloatField(default=38.0, verbose_name='含水量(%)')),
                ('base_curve', models.FloatField(default=8.6, verbose_name='基弧(mm)')),
                ('diameter', models.FloatField(blank=True, default=14.0, verbose_name='直径(mm)')),
                ('purchase_date', models.DateField(verbose_name='购买日期')),
                ('expiry_date', models.DateField(verbose_name='有效期至')),
                ('open_date', models.DateField(blank=True, null=True, verbose_name='开封日期')),
                ('purpose', models.CharField(choices=[('daily', '日常'), ('date', '约会'), ('photo', '拍照')], default='daily', max_length=20, verbose_name='用途')),
                ('status', models.CharField(choices=[('unopened', '未开封'), ('opened', '已开封'), ('used_up', '已用完'), ('expired', '已过期')], default='unopened', max_length=20, verbose_name='状态')),
                ('pair_count', models.IntegerField(default=2, verbose_name='总片数')),
                ('used_count', models.IntegerField(default=0, verbose_name='已用片数')),
                ('notes', models.TextField(blank=True, default='', verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '彩瞳镜片',
                'verbose_name_plural': '彩瞳镜片',
                'db_table': 'lens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WearRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wear_date', models.DateField(verbose_name='佩戴日期')),
                ('duration_hours', models.FloatField(verbose_name='佩戴时长(小时)')),
                ('comfort_level', models.IntegerField(default=3, verbose_name='舒适度(1-5)')),
                ('eye_reaction', models.CharField(choices=[('none', '无不适'), ('dryness', '干涩'), ('redness', '红血丝'), ('fatigue', '视疲劳'), ('dryness_redness', '干涩+红血丝'), ('dryness_fatigue', '干涩+视疲劳'), ('redness_fatigue', '红血丝+视疲劳'), ('all', '全部不适')], default='none', max_length=30, verbose_name='眼部反应')),
                ('notes', models.TextField(blank=True, default='', verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lens', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wear_records', to='lens.lens', verbose_name='镜片')),
            ],
            options={
                'verbose_name': '佩戴记录',
                'verbose_name_plural': '佩戴记录',
                'db_table': 'wear_record',
                'ordering': ['-wear_date', '-created_at'],
            },
        ),
    ]
