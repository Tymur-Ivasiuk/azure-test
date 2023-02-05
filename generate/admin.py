from django.contrib import admin

from .models import *

admin.site.register(Profile)
admin.site.register(Content)
admin.site.register(Questions)
admin.site.register(Answers)
admin.site.register(PoemStyles)
admin.site.register(LetterStyles)
admin.site.register(Tone)
admin.site.register(Length)
admin.site.register(Occasion)
admin.site.register(RelationshipTypes)
admin.site.register(CreditsPrice)
admin.site.register(CreditsBuyPriceAndCount)
admin.site.register(Transactions)