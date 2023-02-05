import openai
from datetime import datetime
import time

from generate.models import *

openai.api_key = "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"

def calculate_years(start_date):
    d1 = datetime.today()

    d2 = datetime.strptime(start_date, "%Y-%m-%d")

    difference = d1.year - d2.year
    if (d1.month, d1.day) < (d2.month, d2.day):
        difference = difference - 1
    return difference

def create_prompt(info, answers):
    prompt = (f'Write a love {info.get("type")} '
              f'in a {info.get("letter_style") if info.get("type") != "Poem" else info.get("poem_style")} '
              f'style and {info.get("tone", "romantic")} tone of voice '
              f'using {info.get("length", "500")} words for '
              f'this occasion: {info.get("occasion")}. '
              f'I am a {info.get("genders")} '
              f'named {info.get("partner_name")} '
              f'who is my {info.get("relationship_type")} '
              f'for the last {calculate_years(info.get("relationship_start_date"))} years. ')

    addition = ''
    if answers:
        questions = Questions.objects.filter(id__in=[int(x) for x in answers.keys()])
        for i in answers.items():
            d = questions.get(id=int(i[0]))
            for j in i[1]:
                addition += f'Try and mention that {d.prompt_text} {j}. '

    final_prompt = prompt + addition
    return final_prompt


def get_ai_response(prompt):
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=2048, temperature=0)
    return response["choices"][0]["text"]


def send_ai_request(info, answers, user):
    prompt = create_prompt(info, answers)
    generated_text = get_ai_response(prompt).strip("\n\n")

    title = f'Your love {info.get("type").lower()} to {info.get("partner_name")}'

    content = Content.objects.create(
        user=user,
        content_type=info.get('type').lower(),
        title=title,
        text=generated_text,
        prompt=prompt,
        answers=answers,
        content_info=info
    )
    user.profile.credits_count -= CreditsPrice.objects.get(credits_type=info.get("type").lower()).credits
    user.save()

    return content.get_absolute_url()

