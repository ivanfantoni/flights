# Flights

The Flights application, available in Italian,  allows users to search for all available Ryanair's flight combinations (round trip) based on the following parameters:

- Departure airport
- Maximum budget
- Departure date
- Return date

## Usage

- ### Holiday Plan

If you want to receive an email with the best Ryanair's flight deals for your vacation days, send me an email like this:

In the subject, write: **Holiday-Plan**
The text should be exactly like this:
Departure airport code, spending threshold, departure date (yyyy-mm-dd), return date (yyyy-mm-dd)

Example:
BGY, 150, 2023-06-01, 2023-06-07

- ### Weekend

If you want to receive roundtrip flights that cost less than €40 for every weekend of the year, send me an email with the subject **subscribe**. If you no longer wish to receive updates, send me an email with **unscribe** in the subject line.

- ### Scheduling

To see all the functions you can schedule with **crontab**:


`python3 flights.py -h`
