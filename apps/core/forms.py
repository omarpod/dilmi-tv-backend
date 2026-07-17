"""apps/core/forms.py"""
from django import forms

from .models import Channel, Match


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
