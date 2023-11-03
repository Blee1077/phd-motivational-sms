import os
import json
import logging
import random
import boto3
import openai
from twilio.rest import Client
from prompts import prompt_list, sys_prompt

logging.getLogger().setLevel(logging.INFO)
s3 = boto3.resource('s3')

def load_json(bucket: str, key: str) -> dict:
    """Loads a JSON file from S3 bucket.
    
    Args:
        bucket (str): S3 bucket containing JSON file
        key (str): Path within bucket of JSON file
        
    Returns:
        dict
    """
    content_object = s3.Object(bucket, key)
    file_content = content_object.get()["Body"].read().decode("utf-8")
    return json.loads(file_content)


def select_prompt(prompt_list: list):
    idx = random.randint(0, len(prompt_list)-1)
    return prompt_list[idx]


def lambda_handler(event, context):
    """Sample pure Lambda function"""
    # Load credentials and secrets
    print(os.environ["SECRET_BUCKET"])
    secrets = load_json(
        bucket=os.environ["SECRET_BUCKET"],
        key=os.environ["SECRET_KEY"]
    )
    twilio_account_sid = secrets.get('twilio_acc_sid')
    twilio_auth_token = secrets.get('twilio_auth_token')
    twilio_number = secrets.get('twilio_num')
    openai_key = secrets.get('openai_key')
    openai.api_key = openai_key

    if event['test'] != "false":
        dest_num = secrets["test_num"]
    else:
        dest_num = secrets["dest_num"]

    # Initialize the Twilio client
    client = Client(twilio_account_sid, twilio_auth_token)

    # Choose prompt for the day
    prompt = select_prompt(prompt_list)
    logging.info(f"Selected prompt: {prompt}")

    # Generate text using the GPT-3.5 model
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use the GPT-3.5 engine
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt},
        ]
    )
    
    # Get the generated text from the response
    generated_text = response.get('choices')[0]["message"]["content"]
    logging.info(f"Generated OpenAI response: {generated_text}")

    # Send the SMS
    message = client.messages.create(
        body=generated_text,
        from_=twilio_number,
        to=dest_num
    )
    logging.info(f"Successfully sent SMS with message SID: {message.sid}")
