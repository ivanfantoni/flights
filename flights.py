from ryanair import Ryanair, airport_utils
import json
from calendar import Calendar
import datetime
from mail import Email
import argparse


ryanair = Ryanair('EUR')

with open("./config.json", 'r') as config:
    reqs = json.load(config)

SUBSCRIBERS = reqs[0]['mail_config']['mailto']
M = Email(server=reqs[0]['mail_config']['server'],
        pop_server=reqs[0]['mail_config']['pop_server'],
        port=int(reqs[0]['mail_config']['port']),
        user_name=reqs[0]['mail_config']['user_name'],
        user=reqs[0]['mail_config']['user'], 
        password=reqs[0]['mail_config']['password'], 
        mailto=','.join(SUBSCRIBERS))

#########################################################################
#                   WEEKEND SUBSCRIPTIONS FUNCTIONS                     #
#########################################################################

def email_list():
    '''
    Print subscribers list.
    '''

    print('')
    for subscriber in SUBSCRIBERS:
        print(subscriber)
    print('')


def subscribe_email(new_email):
    '''
    Adds a new email to the subscribers list.
    '''
    if new_email not in SUBSCRIBERS and '@' in new_email:
        SUBSCRIBERS.append(new_email)  
        with open("./config.json", 'w') as w_config:
            w_reqs = json.dump(reqs, w_config, indent=4)
            print('Email list updated:')
            email_list()
    else:
        if '@' not in new_email:
            print('Email not valid')
        else:
            pass


def unscribe_email(unscrb_email):
    '''
    Delete an email to the suscribers list.
    '''
    if unscrb_email in SUBSCRIBERS and '@' in unscrb_email:
        SUBSCRIBERS.remove(unscrb_email)
        with open("./config.json", 'w') as w_config:
            w_reqs = json.dump(reqs, w_config, indent=4)
            print('Email list updated:')
            email_list()
    else:
        if '@' not in unscrb_email:
            print('Email not valid')
        else:
            pass


#########################################################################
#                       SENDING & READING EMAILS                        #
#########################################################################

def sending_email(subject, body, body_html, message_to=None):
    M.send_email(subject=subject, body=body, body_html=body_html, message_to=message_to) 


def read_emails():
    '''
    Read emails and subscribe or unscribe users from subscriber list.
    '''
    email_list = M.read_email()

    holiday_html = '''
                    <p>Se vuoi ricevere ogni giorno un'email con le migliori offerte per i voli nei tuoi giorni di ferie, <br>inviami un'email così:</p>
                    <p>Nell\'oggetto scrivi: <b>Holiday-Plan</b>
                    <p>Il testo dovrà essere esattamente così:</p>
                    <p>Sigla aeroporto di partenza , soglia di spesa , data di partenza (anno-mese-giorno) , data di ritorno (anno-mese-giorno)</p>
                    <p><b>Esempio:</b>  <br>BGY, 150, 2023-06-01, 2023-06-07</p>
                    '''
    
    for email in email_list:
        if 'subscribe' in email['Subject'].casefold() or 'subscribe' in email['Text'].casefold():
            if email['From'] not in SUBSCRIBERS:
                sending_email(subject='Iscrizione', 
                            body='Ora riceverai ogni giorno le migliori offerte \nSe vuoi annullare la tua iscrizione inviami una e-mail con scritto \'Unscribe\'', 
                            body_html=None, 
                            message_to=email['From'])
                subscribe_email(email['From'])
            else:
                sending_email(subject='Iscrizione', 
                            body='Ehi! Sei già iscritto! \nSe vuoi annullare la tua iscrizione inviami una e-mail con scritto \'Unscribe\'', 
                            body_html=None, 
                            message_to=email['From'])

            M.delete_email(email['Message-ID'])

        elif 'unscribe' in email['Subject'].casefold() or 'unscribe' in email['Text'].casefold():
            if email['From'] in SUBSCRIBERS:
                sending_email(subject='Cancellazione Iscrizione', 
                            body='Arrivederci!',    
                            body_html=None, 
                            message_to=email['From'])
                unscribe_email(email['From'])
            else:
                sending_email(subject='Iscriviti!', 
                            body='Non posso annullare la tua iscrizione \nSe vuoi iscriverti inviami una email con scritto: \'Subscribe\'', 
                            body_html=None, 
                            message_to=email['From'])
                
            M.delete_email(email['Message-ID'])

        elif email['Subject'].casefold() == 'holiday' or email['Text'].casefold() == 'holiday':
            sending_email(subject='Vacanze!', 
                        body='',
                        body_html=holiday_html, 
                        message_to=email['From'])
            M.delete_email(email['Message-ID'])


        elif email['Subject'].casefold() == 'holiday-plan':
            holiday_subscription(email['Text'], email['From'])
            M.delete_email(email['Message-ID'])

        elif email['Subject'].casefold().split(' ')[0] == 'delete-plan':
            delete_holiday_subscription(email['Subject'], email['From'])
            M.delete_email(email['Message-ID'])


    M.close()


#########################################################################
#                      WEEKEND FLIGHTS FUNCTIONS                        #
#########################################################################
     
def weekends_calendar():
    '''
    Create the calendar of all the weekends of the year.
    '''
    wknds=[]
    cal = []
    year = datetime.date.today().year
    year_2 = year + 1
    yrs = [year, year_2]
    for r in yrs:
        yr = r
        cal = Calendar(int(yr)).yeardatescalendar(int(yr), width=12)
        
        for months in cal[0]:
            for month in months:
                dates = {}
                for day in month:
                    if day.weekday() == 5:
                        dates['departureDay'] = day
                    elif day.weekday() == 6:
                        dates['returnDay'] = day

                weekend_list = wknds.append(dates)

    wknds[:]=[x for i, x in enumerate(wknds) if i==wknds.index(x)]
    wknds = wknds[:]
    return wknds


def weekend_flights(wknds):
    '''
    Search all flights for all weekends of the year with a price below the threshold you set.
    '''
    mail_object = 'I Weekend Economici!\n\n'
    email_flights = ''
    html_flight = ''
    for wknd in wknds:
        trips = ryanair.get_return_flights(reqs[1]['origin'], wknd['departureDay'], 
                wknd['departureDay'], wknd['returnDay'], wknd['returnDay'])
        for trip in trips:
            if trip.totalPrice <= float(reqs[1]['generic_treshold']):
                if trip.outbound.departureTime.minute <= 9:
                    ot = str(trip.outbound.departureTime.minute) + "0"
                else:
                    ot = trip.outbound.departureTime.minute
                hour_1 = f'{trip.outbound.departureTime.hour}:{ot}'

                if trip.inbound.departureTime.minute <= 9:
                    it = str(trip.inbound.departureTime.minute) + "0"
                else:
                    it = trip.inbound.departureTime.minute
                hour_2 = f'{trip.inbound.departureTime.hour}:{it}'

                mail_dates = f'{trip.outbound.departureTime.day}-{trip.outbound.departureTime.month}-{trip.outbound.departureTime.year} - {trip.inbound.departureTime.day}-{trip.inbound.departureTime.month}-{trip.inbound.departureTime.year}\n'
                mail_text = f'{trip.outbound.originFull} - {trip.outbound.destinationFull} - A/R \nPrezzo totale: {round(trip.totalPrice, 2)}\n\n'
                hours = f'Ora Andata:{hour_1} - Ora Ritorno:{hour_2}'
                email_tetx = mail_dates + mail_text
                email_flights = email_flights + email_tetx

                html_head = """
                <html>
                    <head></head>
                    <body>"""
                html_text=f"""\
                    <p>{trip.outbound.departureTime.day}-{trip.outbound.departureTime.month}-{trip.outbound.departureTime.year} - {trip.inbound.departureTime.day}-{trip.inbound.departureTime.month}-{trip.inbound.departureTime.year}<br>
                    <b>{trip.outbound.originFull} - {trip.outbound.destinationFull} - A/R</b><br>
                    {hours}<br>
                    Prezzo totale: <b>{round(trip.totalPrice, 2)}</b></p><br>
                """
                html_end = """
                        </body>
                    </html>"""
                html_flight = html_flight + html_text   
                email_flights =  email_flights + email_tetx

    html_message =  html_head + html_flight + html_end      
    text_message = email_flights
    

    for subscriber in SUBSCRIBERS:
        sending_email(subject=mail_object, 
                    body=text_message, 
                    body_html=html_message, 
                    message_to=subscriber)


#########################################################################
#                       HOLIDAY PLANS FUNCTIONS                         #
#########################################################################

def holiday_calendar():
    '''
    Search all flights on specific dates with a price below the threshold you set.
    '''
    for r in reqs[2:]:
        email_flights = ''
        html_flight = ''

        trips = ryanair.get_return_flights(r['origin'], r['origin_date'], 
                r['origin_date'], r['departure_date'], r['departure_date'])
        for trip in trips:
            if trip.totalPrice <= float(r['treshold']):
                if trip.outbound.departureTime.minute <= 9:
                    ot = str(trip.outbound.departureTime.minute) + "0"
                else:
                    ot = trip.outbound.departureTime.minute
                hour_1 = f'{trip.outbound.departureTime.hour}:{ot}'

                if trip.inbound.departureTime.minute <= 9:
                    it = str(trip.inbound.departureTime.minute) + "0"
                else:
                    it = trip.inbound.departureTime.minute
                hour_2 = f'{trip.inbound.departureTime.hour}:{it}'

                mail_dates = f'{trip.outbound.departureTime.day}-{trip.outbound.departureTime.month}-{trip.outbound.departureTime.year} - {trip.inbound.departureTime.day}-{trip.inbound.departureTime.month}-{trip.inbound.departureTime.year}\n'
                mail_text = f'{trip.outbound.originFull} - {trip.outbound.destinationFull} - A/R \nPrezzo totale: {round(trip.totalPrice, 2)}\n\n'
                hours = f'Ora andata:{hour_1} - Ora ritorno:{hour_2}'
                email_tetx = mail_dates + mail_text
                email_flights = email_flights + email_tetx

                html_head = """
                <html>
                    <head></head>
                    <body>"""
                html_text=f"""\
                    <p>{trip.outbound.departureTime.day}-{trip.outbound.departureTime.month}-{trip.outbound.departureTime.year} - {trip.inbound.departureTime.day}-{trip.inbound.departureTime.month}-{trip.inbound.departureTime.year}<br>
                    <b>{trip.outbound.originFull} - {trip.outbound.destinationFull} - A/R</b><br>
                    {hours}<br>
                    Prezzo totale: <b>{round(trip.totalPrice, 2)}</b></p><br>
                """
                html_end = """
                        </body>
                    </html>"""
                html_flight = html_flight + html_text   
                email_flights =  email_flights + email_tetx

        html_message =  html_head + html_flight + html_end      
        text_message = email_flights
        mail_subject = f'Holiday-Plan n°{r["id"]}'

        sending_email(subject=mail_subject, 
                    body=text_message, 
                    body_html=html_message, 
                    message_to=r['user'])


def holiday_subscription(mailtext, user):
    '''Function that adds a new trip customized by the user. 
    The parameters contained in the new journey will be: 
    Id, User, maximum spending threshold and the outbound and return dates.
    '''
    list = mailtext.split(',')
    if _check_params(list=list): 
        params = [item.replace(' ', '')[:10] if len(item) > 10 else item.replace(' ', '') for item in list][:4]
        if _check_iata(params[0]):
            od, dd =  _check_date([params[2], params[3]])
            if od:
                holiday_config = {
                "id": reqs[1]['unique_number'],
                "user": user,
                "origin": params[0].upper(),
                "treshold": params[1],
                "origin_date": od,
                "departure_date": dd,
                }
                reqs[1]['unique_number'] = int(reqs[1]['unique_number']) +1 
                reqs.append(holiday_config)
                with open("./config.json", 'w') as w_config:
                    holiday_sub = json.dump(reqs, w_config, indent=4)
                _confirm_holiday_plan(holiday_config)
            else:
                _error_holiday_plan(date=d[1], user=user)
        else:
            _error_iata_code(iata=params[0].upper(), user=user)
    else:
        _error_params(user=user)


def delete_holiday_subscription(mailsubject, user):
    global reqs

    id = mailsubject.split(' ')[1]
    configfile = []
    count = 0

    for plan in reqs:
        try:
            if plan['id'] != int(id):
                configfile.append(plan)
            else:
                if plan['id'] == int(id) and plan['user'] == user:
                    count += 1
                else:
                    configfile.append(plan)
        except KeyError:
            configfile.append(plan)

    if count == 0:
        body_html=f'''
                <p>Non ho trovato nessun <b>Holiday-Plan</b> con iscrizione n°{id}.</p>
        '''
    else:
        body_html=f'''
                <h2><b>Annullamento eseguito!</b></h2><br>
                <p>L\'<b>Holiday-Plan</b> n°{id} è stato annullato!<br><br>
                A Presto!</p>'''
        
    with open("./config.json", 'w') as w_config:
        json.dump(configfile, w_config, indent=4)
    with open("./config.json", 'r') as config:
        reqs = json.load(config)


    sending_email(subject=f'Annullamento Holiday-Plan n°{id}',
                message_to=user,
                body_html=body_html, body='')


#########################################################################
#                     CHECKING FOR ERRORS FUNCTIONS                     #
#########################################################################

def _check_expiring_plan():
    '''
    Check if there are any expired Holiday-Plans.
    '''
    try:
        for plan in reqs[2:]:
            if _check_date([plan['origin_date'], plan['departure_date']]):
                pass
            else:
                _delete_plan_expired(plan=plan)
                _expired_plan_email(plan=plan)
    except KeyError:
        pass


def _delete_plan_expired(plan):
    '''
    Delete expired Holiday Plans.
    '''
    global reqs

    id = plan['id']
    configfile = []

    for plan in reqs:
        try:
            if plan['id'] != int(id):
                configfile.append(plan)
            else:
                if plan['id'] == int(id):
                    pass
                else:
                    configfile.append(plan)
        except KeyError:
            configfile.append(plan)
        
    with open("./config.json", 'w') as w_config:
        json.dump(configfile, w_config, indent=4)
    with open("./config.json", 'r') as config:
        reqs = json.load(config)


def _expired_plan_email(plan):
    '''
    Send an email if the Holiday-Plan has expired.
    '''

    body_html = f'''
                <p>Ciao, il tuo <b>Holiday-Plan</b> n°{plan["id"]} è scaduto e tu dovresti essere già in vacanza.<br>
                A presto e <b>Buon Viaggio!</b>'''

    subject = f'Holiday-Plan n°{plan["id"]} -- SCADUTO!'

    sending_email(subject=subject,
                  message_to=plan['user'],
                  body_html=body_html, body='')


def _confirm_holiday_plan(holiday_config):
    '''
    Send a confirmation email to subscribe to a new Holiday-Plan
    '''
    body_html = f'''
                    <h2><b>Welcome!!!</b></h2>
                    D\'ora in poi riceverai ogni giorno le offerte per questo <b>Holiday-Plan</b><br>
                    <p>Aeroporto di partenza: {holiday_config["origin"]}<br>
                    Data di partenza: {holiday_config["origin_date"]}<br>
                    Data di rientro: {holiday_config["departure_date"]}<br>
                    Soglia massima: €{holiday_config["treshold"]}<br><br>
                    Se non volessi più ricevere aggionamenti in merito a queste date<br>
                    Mandami una email e nell\'oggetto scrivi: <b>Delete-Plan {holiday_config['id']}</b></p>'''

    subject = f'Iscrizione a Holiday-Plan n°{holiday_config["id"]}'
    sending_email(subject=subject,
                  message_to=holiday_config['user'],
                  body_html=body_html, body='')


def _error_holiday_plan(date, user):
    '''
    Send an error email if the date requested for the Holiday-Plan is before today's date
    '''
    
    body_html = f'''
                <p>Non puoi inserire un Holiday-Plan con una data di partenza già passata\n
                o una data di rientro antecedente alla data di partenza!!!\n\n
                Prova a controllare questa/e date:\n
                {date[0]} - {date[1]}'''

    subject = f'Qualcosa è andato storto!'

    sending_email(subject=subject,
                  message_to=user,
                  body_html=body_html, body='')


def _split_dates(dates: list):
    '''
    Splits the list of dates and returns them in "date" format.
    '''
    splits = []
    for date in dates:
        y, m, d = date.split('-')
        m = _zero_nine(m)
        d = _zero_nine(d)
        split = datetime.date(int(y), int(m), int(d))
        splits.append(split)
    return splits


def _zero_nine(number):
    if int(number) < 10 and len(number) == 1:
        number = f'0{number}'
    return number


def _check_date(dates: list):
    '''
    Check that the date entered is not before today's date 
    and that the return date is no earlier than the departure date.
    '''
    today = datetime.date.today()
    dt = _split_dates(dates)
    checked_dates = ['', '']
    if dt[0] < today:
        result = False
        checked_dates[0] = f'Data di Partenza {dt[0]}'
    elif dt[1] < dt[0]:
        result = False
        checked_dates[1] = f'Data di rientro {dt[1]}'
    else:
        result = True

    return result, checked_dates


def _check_iata(iata_code: str):
    '''
    Check if the iata code exists.
    '''
    apt =  airport_utils.AIRPORTS
    try:
        if apt[iata_code.upper()]:
            return True
        else:
            return False
    except KeyError:
        return False


def _error_iata_code(iata: str, user: str):
    '''
    Send an error email if the iata code does not exist.
    '''
    body_html = f'''
                <p>Non esiste nessun aeroporto con sigla <b>{iata}</b>'''

    subject = f'Qualcosa è andato storto!'

    sending_email(subject=subject,
                  message_to=user,
                  body_html=body_html, body='')
 

def _check_params(list: list):
    '''
    Check that all parameters have been entered.
    '''
    if len(list) >= 4:
        return True
    else:
        return False


def _error_params(user: str):
    '''
    Send an error email if not all parameters have been entered.
    '''
    body_html = f'''
                <h2>Manca qualche parametro!</h2>
                <p>Se vuoi ricevere ogni giorno un'email con le migliori offerte per i voli nei tuoi giorni di ferie, <br>inviami un'email così:</p>
                    <p>Nell\'oggetto scrivi: <b>Holiday-Plan</b>
                    <p>Il testo dovrà essere esattamente così:</p>
                    <p>Sigla aeroporto di partenza , soglia di spesa , data di partenza (anno-mese-giorno) , data di ritorno (anno-mese-giorno)</p>
                    <p><b>Esempio:</b>  <br>BGY, 150, 2023-06-01, 2023-06-07</p>'''

    subject = f'Qualcosa è andato storto!'

    sending_email(subject=subject,
                  message_to=user,
                  body_html=body_html, body='')


parser = argparse.ArgumentParser(description='Sending emails with Ryanair flight prices related to the parameters set in the config.json file')
group = parser.add_mutually_exclusive_group()
group.add_argument('-w', '--weekends', help='Search for flights for all weekends of the year with the price threshold set in the config.json file', action='store_true')
group.add_argument('-v', '--vacation', help='Search flights for dates set in the config.json file', action='store_true')
group.add_argument('-el', '--emaillist', help='Print all email', action='store_true')
group.add_argument('-s', '--subscribe', help='Add new email to contact list', action='store')
group.add_argument('-u', '--unscribe', help='Delete email to contact list', action='store', )
group.add_argument('-r', '--read', help='Read Email list', action='store_true', )
group.add_argument('-d', '--date', help='Check Holiday-Plan dates', action='store_true', )

args = parser.parse_args()

if args.weekends:
    weekend_flights(weekends_calendar())
elif args.vacation:
    holiday_calendar()
elif args.emaillist:
    email_list()
elif args.subscribe:
    subscribe_email(args.subscribe)
elif args.unscribe:
    unscribe_email(args.unscribe)
elif args.read:
    read_emails()
elif args.date:
    _check_expiring_plan()
else:
    pass