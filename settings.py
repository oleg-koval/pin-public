# -*- coding: utf8 -*-
import os

try:
    import local_settings
    params = local_settings.params
except Exception:
	params = {
        'dbn': 'postgres',
        'db': 'pin',
        'user': os.environ['DB_USER'],
        'pw': os.environ['DB_PASSWORD'],
        'host': os.environ['DB_HOST'],
        }
        redis = {
        'host': 'localhost',
        'port': 6379,
        'db': 3,
        }

FACEBOOK = {'application_id': '1540569082835261',
            'application_secret': os.environ['FACEBOOK_APPLICATION_SECRET'],
            }

TWITTER = {'api_key': 'QNcMlvWvVS2ictFpHW3bQ',
           'api_secret': os.environ['TWITTER_APPLICATION_SECRET'],
           }

GOOGLE = {'client_id': '985703411904-602sd2jgsl6v5ad8k3fb6tanc46a0v88.apps.googleusercontent.com',
          'client_secret': os.environ['GPLUS_APPLICATION_SECRET'],
          }

BING = {
    'customer_id': '7e41d6a8-1914-4354-bf31-3abd36cb0179',
    'account_key': os.environ['BING_APPLICATION_SECRET']
}

LANGUAGES = (('en', 'English'),
             ('fr', 'Français'),
             ('es', 'Español'),
             )

COUNTRIES = [
    'United States', 'Canada', 'Afghanistan', 'Aland Islands', 'Albania', 'Algeria', 'American Samoa', 'Andorra', 'Angola', 'Anguilla', 'Antarctica', 'Antigua and Barbuda', 'Argentina', 'Armenia', 'Aruba', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh',
    'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bermuda', 'Bhutan', 'Bolivia, Plurinational State of', 'Bonaire, Sint Eustatius and Saba', 'Bosnia and Herzegovina', 'Botswana', 'Bouvet Island', 'Brazil', 'British Indian Ocean Territory',
    'Brunei Darussalam', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon', 'Cape Verde', 'Cayman Islands', 'Central African Republic', 'Chad', 'Chile',
    'China', 'Christmas Island', 'Cocos (keeling) Islands', 'Colombia', 'Comoros', 'Congo', 'Congo, Democratic Republic of The', 'Cook Islands', 'Costa Rica', 'Cote Divoire',
    'Croatia', 'Cuba', 'Curacao', 'Cyprus', 'Czech Republic', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Ethiopia', 'Falkland Islands (malvinas)', 'Faroe Islands', 'Fiji', 'Finland',
    'France', 'French Guiana', 'French Polynesia', 'French Southern Territories', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Gibraltar', 'Greece', 'Greenland', 'Grenada', 'Guadeloupe', 'Guam', 'Guatemala', 'Guernsey', 'Guinea', 'Guinea-bissau', 'Guyana', 'Haiti', 'Heard Island and Mcdonald Islands', 'Holy See (Vatican City State)', 'Honduras',
    'Hong Kong', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq', 'Ireland', 'Isle of Man', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jersey', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati', 'Korea, North', 'Korea, South',
    'Kuwait', 'Kyrgyzstan', 'Lao People&#;s Democratic Republic', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Macao', 'Macedonia', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Martinique', 'Mauritania',
    'Mauritius', 'Mayotte', 'Mexico', 'Micronesia, Federated States of', 'Moldova, Republic of', 'Monaco', 'Mongolia', 'Montenegro', 'Montserrat', 'Morocco',
    'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal',
    'Netherlands', 'New Caledonia', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Niue', 'Norfolk Island',
    'Northern Mariana Islands', 'Norway', 'Oman', 'Pakistan', 'Palau', 'Palestinian Territory', 'Panama', 'Papua New Guinea', 'Paraguay',
    'Peru', 'Philippines', 'Pitcairn', 'Poland', 'Portugal', 'Puerto Rico', 'Qatar', 'Reunion', 'Romania', 'Russian Federation', 'Rwanda',
    'Samoa', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore', 'Sint Maarten (dutch Part)', 'Slovakia', 'Slovenia', 'Solomon Islands', 'Somalia',
    'South Africa', 'South Georgia', 'South Sudan', 'Spain', 'Sri Lanka', 'St. Barthelemy', 'St. Helena', 'St. Kitts And Nevis', 'St. Lucia', 'St. Martin (french Part)', 'St. Pierre And Miquelon', 'St. Vincent And The Grenadines', 'Sudan', 'Suriname', 'Svalbard and Jan Mayen', 'Swaziland', 'Sweden', 'Switzerland', 'Syrian Arab Republic', 'Taiwan, Province of China',
    'Tajikistan', 'Tanzania, United Republic of', 'Thailand', 'Timor-leste', 'Togo', 'Tokelau', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Turks and Caicos Islands', 'Tuvalu', 'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States Minor Outlying Islands', 'Uruguay',
    'Uzbekistan', 'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam',
    'Virgin Islands, British', 'Virgin Islands, U.s.', 'Wallis and Futuna', 'Western Sahara', 'Yemen', 'Zambia', 'Zimbabwe',
]

PIN_COUNT = 50
SEARCH_PINS = True

API_URL = os.environ['API_URL'] if 'API_URL' in os.environ else "http://mypinnings.com/"
PIN_NEW_DAYS = 7
MEDIA_PATH = "static/tmp"
