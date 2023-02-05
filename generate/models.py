from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField

from generate.validators import validate_positive


def get_user_email(self):
    return self.email
User.add_to_class("__str__", get_user_email)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits_count = models.PositiveIntegerField(default=0)
    phone_number = PhoneNumberField(null=True, blank=True, unique=True)
    partner_email = models.EmailField(null=True, blank=True)
    partner_phone_number = PhoneNumberField(null=True, blank=True)

    not_anonim = models.BooleanField(default=False)

    save_answers = models.JSONField(default={})

    def __str__(self):
        return self.user.email

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


class Content(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    types = [
        ('letter', 'letter'),
        ('poem', 'poem'),
        ('note', 'note'),
    ]
    content_type = models.CharField(max_length=50, choices=types)

    title = models.CharField(max_length=255)
    text = models.TextField()

    prompt = models.TextField()
    answers = models.JSONField()
    content_info = models.JSONField()

    time_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('content', kwargs={'content_id': self.id})



class Questions(models.Model):
    question = models.CharField(max_length=255)
    prompt_text = models.CharField(max_length=255)

    def __str__(self):
        return self.question


class Answers(models.Model):
    answer = models.CharField(max_length=255)
    question = models.ForeignKey('Questions', on_delete=models.CASCADE)

    def __str__(self):
        return self.answer


class PoemStyles(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class LetterStyles(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Tone(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Length(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Occasion(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class RelationshipTypes(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class CreditsPrice(models.Model):
    credits = models.PositiveIntegerField(default=1)

    types = [
        ('letter', 'letter'),
        ('poem', 'poem'),
        ('note', 'note'),
    ]
    credits_type = models.CharField(max_length=50, choices=types)

    def __str__(self):
        return self.credits_type


class CreditsBuyPriceAndCount(models.Model):
    credits_count = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=7, decimal_places=2, validators=[validate_positive])

    def __str__(self):
        return str(self.credits_count)


class Transactions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    credits_count = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=7, decimal_places=2, validators=[validate_positive])

    time_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user.email)

