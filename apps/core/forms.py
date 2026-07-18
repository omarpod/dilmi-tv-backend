"""apps/core/forms.py"""
from django import forms
from django.contrib.auth.models import User

from .models import Channel, Match, News, SiteSettings


class QuickMatchForm(forms.ModelForm):
    """
    نموذج إضافة سريعة — يدوي بالكامل، لا علاقة له بـ RapidAPI أو أي
    مصدر آلي. الهدف "أقل من 10 ثوانٍ لكل مباراة": حقول قليلة، الحقول
    الاختيارية فعلاً اختيارية (لا شعارات، لا نتيجة أولية)، وbeginning
    focus + رسالة نجاح تعيد المستخدم لنفس الصفحة فوراً لإدخال التالية
    (راجع quick_add_match في apps/dashboard/views.py).
    """

    class Meta:
        model = Match
        fields = ['home_team', 'away_team', 'competition', 'match_datetime', 'channel', 'status']
        widgets = {
            'home_team': forms.TextInput(attrs={'autofocus': True, 'placeholder': 'مثال: الأهلي'}),
            'away_team': forms.TextInput(attrs={'placeholder': 'مثال: الزمالك'}),
            'competition': forms.TextInput(attrs={'placeholder': 'اختياري — مثال: الدوري المصري'}),
            'match_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
        labels = {
            'home_team': 'الفريق المضيف',
            'away_team': 'الفريق الضيف',
            'competition': 'البطولة (اختياري)',
            'match_datetime': 'موعد المباراة',
            'channel': 'قناة البث (اختياري)',
            'status': 'الحالة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['competition'].required = False
        self.fields['channel'].required = False
        self.fields['channel'].queryset = Channel.objects.filter(is_active=True)
        self.fields['channel'].empty_label = 'بدون قناة (يُضاف لاحقاً)'


class MatchEditForm(forms.ModelForm):
    """نموذج تعديل كامل لمباراة موجودة — يشمل النتيجة والدقيقة والشعارين،
    خلافاً لنموذج الإضافة السريعة. الحالة (status) قابلة للتعديل هنا
    يدوياً كتجاوز صريح، رغم أن دورة الحياة التلقائية بالوقت (راجع
    apps/core/tasks.py) تُدير المباريات المُضافة يدوياً تلقائياً أصلاً —
    هذا الحقل هنا لتصحيح استثناء عاجل فقط (مباراة مؤجَّلة مثلاً)."""

    class Meta:
        model = Match
        fields = [
            'home_team', 'away_team', 'home_team_logo_url', 'away_team_logo_url',
            'competition', 'match_datetime', 'channel', 'stream_url', 'status',
            'home_score', 'away_score', 'elapsed_minutes',
        ]
        widgets = {
            'match_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
        labels = {
            'home_team': 'الفريق المضيف',
            'away_team': 'الفريق الضيف',
            'home_team_logo_url': 'شعار الفريق المضيف (رابط)',
            'away_team_logo_url': 'شعار الفريق الضيف (رابط)',
            'competition': 'البطولة',
            'match_datetime': 'موعد المباراة',
            'channel': 'قناة البث',
            'stream_url': 'رابط البث المباشر لهذه المباراة (اختياري)',
            'status': 'الحالة',
            'home_score': 'أهداف المضيف',
            'away_score': 'أهداف الضيف',
            'elapsed_minutes': 'الدقيقة الحالية',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['competition'].required = False
        self.fields['home_team_logo_url'].required = False
        self.fields['away_team_logo_url'].required = False
        self.fields['stream_url'].required = False
        self.fields['channel'].required = False
        self.fields['channel'].queryset = Channel.objects.filter(is_active=True)
        self.fields['channel'].empty_label = 'بدون قناة'
        # يعرض القيمة الحالية بصيغة datetime-local الصحيحة عند التعديل
        if self.instance and self.instance.pk:
            self.initial['match_datetime'] = self.instance.match_datetime.strftime('%Y-%m-%dT%H:%M')


class AdsSettingsForm(forms.ModelForm):
    """نموذج إعدادات شبكات الإعلانات — صف وحيد (SiteSettings.get_solo)،
    يُقرأ من تطبيق Flutter عبر /api/app-config/. كل الحقول اختيارية:
    ترك حقل فارغاً يعني عدم عرض إعلانات تلك الشبكة في التطبيق."""

    class Meta:
        model = SiteSettings
        fields = [
            'ads_enabled',
            'admob_enabled', 'admob_app_id', 'admob_banner_ad_unit_id',
            'admob_interstitial_ad_unit_id', 'admob_rewarded_ad_unit_id',
            'facebook_ads_enabled', 'facebook_ads_placement_id',
            'facebook_ads_interstitial_placement_id', 'facebook_ads_rewarded_placement_id',
            'other_ads_enabled', 'other_ad_network_name',
            'other_ad_banner_id', 'other_ad_interstitial_id', 'other_ad_rewarded_id',
            'app_ads_txt',
        ]
        widgets = {
            'app_ads_txt': forms.Textarea(attrs={'rows': 5, 'placeholder': 'google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0'}),
        }
        labels = {
            'ads_enabled': 'تفعيل الإعلانات في التطبيق (المفتاح الرئيسي)',
            'admob_enabled': 'تفعيل AdMob',
            'admob_app_id': 'AdMob — معرّف التطبيق (App ID)',
            'admob_banner_ad_unit_id': 'AdMob — معرّف إعلان البانر (Banner)',
            'admob_interstitial_ad_unit_id': 'AdMob — معرّف الإعلان البيني (Interstitial)',
            'admob_rewarded_ad_unit_id': 'AdMob — معرّف الإعلان المكافأ (Rewarded)',
            'facebook_ads_enabled': 'تفعيل Meta / Facebook Audience Network',
            'facebook_ads_placement_id': 'Facebook — معرّف موضع البانر (Banner)',
            'facebook_ads_interstitial_placement_id': 'Facebook — معرّف موضع الإعلان البيني (Interstitial)',
            'facebook_ads_rewarded_placement_id': 'Facebook — معرّف موضع الإعلان المكافأ (Rewarded)',
            'other_ads_enabled': 'تفعيل شبكة إعلانية أخرى',
            'other_ad_network_name': 'اسم الشبكة الإعلانية الأخرى',
            'other_ad_banner_id': 'الشبكة الأخرى — معرّف إعلان البانر (Banner)',
            'other_ad_interstitial_id': 'الشبكة الأخرى — معرّف الإعلان البيني (Interstitial)',
            'other_ad_rewarded_id': 'الشبكة الأخرى — معرّف الإعلان المكافأ (Rewarded)',
            'app_ads_txt': 'محتوى ملف app-ads.txt',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if not field_name.endswith('_enabled'):
                self.fields[field_name].required = False


class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'logo', 'category', 'is_active', 'order']
        labels = {
            'name': 'اسم القناة',
            'logo': 'شعار القناة',
            'category': 'التصنيف',
            'is_active': 'نشِطة؟',
            'order': 'ترتيب الظهور',
        }


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = [
            'title', 'content', 'image', 'external_image_url', 'source_url',
            'related_match', 'status', 'publish_at', 'archive_at',
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8}),
            'publish_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'archive_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
        labels = {
            'title': 'العنوان',
            'content': 'المحتوى',
            'image': 'صورة (رفع مباشر)',
            'external_image_url': 'رابط صورة خارجي',
            'source_url': 'رابط المصدر',
            'related_match': 'مرتبط بمباراة (اختياري)',
            'status': 'الحالة',
            'publish_at': 'وقت النشر المجدول (اختياري)',
            'archive_at': 'وقت الأرشفة التلقائية (اختياري)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['image', 'external_image_url', 'source_url', 'related_match', 'publish_at', 'archive_at']:
            self.fields[field_name].required = False
        if self.instance and self.instance.pk and self.instance.publish_at:
            self.initial['publish_at'] = self.instance.publish_at.strftime('%Y-%m-%dT%H:%M')
        if self.instance and self.instance.pk and self.instance.archive_at:
            self.initial['archive_at'] = self.instance.archive_at.strftime('%Y-%m-%dT%H:%M')


class StaffUserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='كلمة المرور', min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff', 'is_active']
        labels = {
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'is_staff': 'موظف (وصول للوحة التحكم)؟',
            'is_active': 'نشِط؟',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_staff'].initial = True
        self.fields['is_active'].initial = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class StaffUserEditForm(forms.ModelForm):
    new_password = forms.CharField(
        widget=forms.PasswordInput, required=False, min_length=8,
        label='كلمة مرور جديدة (اختياري)',
        help_text='اتركه فارغاً لعدم تغيير كلمة المرور الحالية.',
    )

    class Meta:
        model = User
        fields = ['email', 'is_staff', 'is_active']
        labels = {
            'email': 'البريد الإلكتروني',
            'is_staff': 'موظف (وصول للوحة التحكم)؟',
            'is_active': 'نشِط؟',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user
