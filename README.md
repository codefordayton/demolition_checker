# Demolition Notifications

## About the Project

This is a small project to support [Preservation Dayton](https://www.preservationdayton.com/). It monitors demolition permits for the city of Dayton and sends emails when it detects a change.

This is a small application that submits a webform request daily to the [Online Permit Search for Building Services](https://aca-prod.accela.com/DAYTON/Cap/CapHome.aspx?module=Building&TabName=Building). It submits 2 requests, one for commercial and one residential properties. If there are results, it emails them to an interested party.

## Installation

This application is a small Python application that uses the [Scrapy](https://scrapy.org/) framework to submit webforms. It analyzes the results and, if necessary, sends an email via the MailTrap api.

You need a Python 3 environment to run this, unless someone wants to submit a PR to Dockerize the application. :)

To run it:

* Create a virtual environment using a Python 3 (I used 3.11.6) with `virtualenv env -ppython3`

* Activate the environment with `source env/bin/activate`

* Install the requirements with `pip install -r requirements.txt`

The application can be run via the scrapy command: `scrapy runspider main.py`

## Next Steps

We started this project on at our meeting on August 6th. It is ripe for submissions.

Here are a few places that need to be worked. Check the issues for more detailed descriptions.

1. Add table parsing to determine information about the properties that were added to the list. This should be pulled into a python dict that can be fed into a Jinja template for the email.

2. Build out the operation chain. Scrapy works via a sequence of methods that call back to the next one based on request completion. The test sequence we set up is:

a) Open the form and submit the request for residential properties (`parse` method).

b) Parse the response from the initial form request to determine if there were permits submitted that day (`parseResults` method).

This is a start, but we need to add at least one more step in the chain. Since the form remains on the screen with the results, we can submit the request for Commercial Wrecking Permits at the end of the `parseResults` method.

The next callback should do a couple of actions:

a) Parse the table to determine if there are commercial properties that should be added to the python dict.

b) If there is anything in the dict send an email to the interested party. This is done [here](https://github.com/codefordayton/dhrn-address-lookup/blob/main/dhrn-functions/packages/dhrn/sendmail/__main__.py) if you'd like to see an example.

c) If an error occurred, send an email to `team@codefordayton.org` so we can troubleshoot it. This is really important! Filling out the form via parsing the html is necessary but brittle. If they change the form in a way that breaks the submission, we'd like to know about it. :)

3. Integrate the email sending functionality mentioned above.

4. Clean up the code. Scrapy code (like a lot of automation code) tends to get messy quickly. Try to clean it up so that it is understandable and relies less on the various field ids and xpath formulas being embedded in the middle of the code.

5. Figure out deployment and Cron functionality (Dave'll probably do this one)

## Questions

Ask me (Dave Best) if you'd like commit-bit on the repo. Otherwise, feel free to fork the repository and submit merge requests.