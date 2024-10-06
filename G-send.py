import os
import random
import time
import smtplib
import string
import re
import datetime
import threading
import dns.resolver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from transformers import pipeline

# Load the GPT-2 model
generator = pipeline('text-generation', model='gpt2')

# Semaphore for controlling concurrent threads
max_concurrent_threads = 20
semaphore = threading.Semaphore(max_concurrent_threads)

# Configuration Parameters
BCC_COUNT = 1  # Number of emails to send per batch
DOMAINS_LIST = [
    'cool-backgrounds.org', 'wsulaw.com', 'themrsbox.com', 'cancelpage.com',
    'happyturtle.ca', 'softactivity.com', 'gxjbsj.com', 'dnstechpack.com'
]
RANDOM_WORDS_LIST = ['info', 'admin', 'support', 'hello', 'newsletter']
SUBJECT_WORDS_LIST = [
    "Update", "Reminder", "Invitation", "Newsletter", "Announcement",
    "Opportunity", "Feedback", "Request", "Alert", "Report"
]
ERROR_PATTERNS = {
    '554': "spam block",
    '550': "user does not exist",
    '552': "user over quota",
}

# Utility Functions
def generate_random_string(length, char_type):
    char_sets = {
        'an': string.ascii_letters + string.digits,
        'n': string.digits,
        'a': string.ascii_letters
    }
    return ''.join(random.choices(char_sets[char_type], k=length))

def generate_from_name():
    base_name = random.choice(['Alex', 'Emma', 'Jack', 'Sophia', 'Noah', 'Olivia', 'William', 'Ava'])
    return f"{base_name}{generate_random_string(2, 'n')}" if random.random() > 0.3 else f"{base_name}_{generate_random_string(2, 'a')}"

def replace_tags(text):
    date_string = datetime.date.today().strftime('%Y-%m-%d')
    text = re.sub(r'\[mail_date\]', date_string, text)
    pattern = r'\[(an|n|a)_(\d+)\]'
    while match := re.search(pattern, text):
        char_type, length_str = match.groups()
        text = text[:match.start()] + generate_random_string(int(length_str), char_type) + text[match.end():]
    return text

def get_mx_record(domain):
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return str(mx_records[0].exchange).rstrip('.')
    except Exception as e:
        print(f"Failed to resolve MX record for {domain}: {e}")
        return None

def generate_gpt2_text(prompt, max_length=5):
    return generator(prompt, max_length=max_length, num_return_sequences=1)[0]['generated_text'].strip()

def generate_subject_with_random_variations():
    base_subject = random.choice(SUBJECT_WORDS_LIST)
    base_subject += f" {generate_random_string(2, 'n')}" if random.random() > 0.3 else ""
    base_subject += f" {random.choice(['!', '?', '.'])}" if random.random() > 0.3 else ""
    return base_subject + f" {random.choice(['©', '™', '✓'])}"

def read_file_content(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist")
    with open(file_path, 'r') as file:
        return file.read()

def analyze_error(error_message):
    for code, description in ERROR_PATTERNS.items():
        if code in str(error_message):
            print(f"Error detected: {code} - {description}")
            if description == "spam block":
                return generate_subject_with_random_variations() + ''.join(random.choice('!@#$%^&*()') for _ in range(3))
            elif description == "user does not exist":
                return None
            elif description == "user over quota":
                return None
    return None

# Email Sending Function
def send_emails(bcc_emails):
    if not bcc_emails:
        return

    selected_domain = random.choice(DOMAINS_LIST)
    random_word = random.choice(RANDOM_WORDS_LIST)
    domain = bcc_emails[0].split('@')[1]
    mx_record = get_mx_record(domain)
    
    if not mx_record:
        return

    random_return_path = f"{generate_random_string(10, 'n')}@{selected_domain}"
    msg = MIMEMultipart()
    msg['From'] = f"{generate_from_name()} <{random_return_path}>"
    msg['To'] = f'{random_word}{generate_random_string(8, "an")}@{selected_domain}'
    msg['Bcc'] = ', '.join(bcc_emails)
    msg['Subject'] = generate_subject_with_random_variations()

    # Attach message content
    full_message = read_file_content('header.txt') + "\n\n" + read_file_content('html.txt')
    msg.attach(MIMEText(full_message, 'html'))
    msg['Message-ID'] = f"<{generate_random_string(20, 'an')}@{selected_domain}>"

    with semaphore:
        try:
            random_subdomain = generate_random_string(18, 'an')
            local_hostname = f'{random_subdomain}.{selected_domain}'
            with smtplib.SMTP(mx_record, local_hostname=local_hostname) as smtp_server:
                smtp_server.sendmail(random_return_path, [msg['To']] + bcc_emails, msg.as_string())
            print(f"Batch of {len(bcc_emails)} emails sent successfully!")
        except Exception as e:
            error_action = analyze_error(e)
            print(f"Failed to send batch of {len(bcc_emails)} emails. Error: {e}. Suggested action: {error_action}")

# Main Execution
data = read_file_content('data.txt').splitlines()
data_count = 0
while data_count < len(data):
    bcc_emails = [data[i].strip() for i in range(data_count, min(data_count + BCC_COUNT, len(data)))]
    data_count += BCC_COUNT
    threading.Thread(target=send_emails, args=(bcc_emails,)).start()
    time.sleep(random.uniform(5, 10))  # Simulate natural sending behavior