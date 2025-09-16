from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from music_ministry.models import Member
import csv
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Add users with default passwords and generate credentials list'

    def handle(self, *args, **options):
        # Default password for all users
        default_password = "MMAS2024!"
        
        # User data: email, username, fullname, role
        users_data = [
            ("angelheavenanastacio@gmail.com", "angel", "Angelica Anastacio", "Worship Leader"),
            ("salvatierralowel739@gmail.com", "lowel", "Lowel Salvatierra", "Bassist"),
            ("irishjrlbl@gmail.com", "irish", "Irish Juralbal", "Worship leader"),
            ("joylinejocosol1983@gmail.com", "joy", "Joy Jocosol", "Worship Leader"),
            ("gomezdawnaubreu@gmail.com", "aubrey", "Aubrey Gomez", "Worship Leader"),
            ("dreijocosol@gmail.com", "shayne", "Shayne Jocosol", "Drummer"),
            ("teacherbert85@gmail.com", "bert", "Bert Yruma", "Keys"),
            ("secondhandserenade38@gmail.com", "angelo", "Angelo Miranda", "Worship Leader"),
            ("kenneth@gmail.com", "kenneth", "Kenneth Mangaya", "Drummer"),
            ("cornelioluib@gmail.com", "nel", "Cornelio P. Luib", "Drummer"),
        ]
        
        # Role mapping from provided roles to model choices
        role_mapping = {
            "Worship Leader": "worship_leader",
            "Worship leader": "worship_leader",  # Handle case variation
            "Bassist": "bassist",
            "Drummer": "drummer",
            "Keys": "keys",
            "Guitarist": "guitarist",
            "Vocalist": "vocalist",
        }
        
        created_users = []
        credentials_list = []
        
        self.stdout.write(self.style.SUCCESS('Starting user creation process...'))
        
        for email, username, fullname, role in users_data:
            try:
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.WARNING(f'User {username} already exists. Skipping...')
                    )
                    continue
                
                if User.objects.filter(email=email).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Email {email} already exists. Skipping...')
                    )
                    continue
                
                # Map role to model choice
                musician_role = role_mapping.get(role, "vocalist")  # Default to vocalist if not found
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=default_password,
                    first_name=fullname.split()[0] if fullname.split() else "",
                    last_name=" ".join(fullname.split()[1:]) if len(fullname.split()) > 1 else ""
                )
                
                # Create member profile
                member = Member.objects.create(
                    user=user,
                    name=fullname,
                    email=email,
                    musician_role=musician_role
                )
                
                created_users.append({
                    'username': username,
                    'email': email,
                    'fullname': fullname,
                    'role': role,
                    'musician_role': musician_role
                })
                
                credentials_list.append({
                    'username': username,
                    'password': default_password
                })
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created user: {username} ({fullname}) - {role}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error creating user {username}: {str(e)}')
                )
        
        # Generate credentials CSV file
        credentials_file = 'user_credentials.csv'
        try:
            with open(credentials_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['username', 'password']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for cred in credentials_list:
                    writer.writerow(cred)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Credentials saved to: {credentials_file}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error saving credentials file: {str(e)}')
            )
        
        # Display summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('USER CREATION SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Total users processed: {len(users_data)}')
        self.stdout.write(f'Users created: {len(created_users)}')
        self.stdout.write(f'Default password: {default_password}')
        self.stdout.write(f'Credentials file: {credentials_file}')
        
        if created_users:
            self.stdout.write(self.style.SUCCESS('\nCreated Users:'))
            for user in created_users:
                self.stdout.write(f'  • {user["username"]} ({user["fullname"]}) - {user["role"]}')
        
        self.stdout.write(self.style.SUCCESS('\nCredentials List:'))
        for cred in credentials_list:
            self.stdout.write(f'  • Username: {cred["username"]}, Password: {cred["password"]}')
