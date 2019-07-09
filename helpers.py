import xml.etree.ElementTree as ElementTree
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%dT%H%M"


def flight_xml_to_dict(xml_flight):
    carrier = xml_flight.find('./Carrier')
    return {
        'Carrier': carrier.text,
        'CarrierId': carrier.attrib['id'],
        'FlightNumber': xml_flight.find('./FlightNumber').text,
        'Source': xml_flight.find('./Source').text,
        'Destination': xml_flight.find('./Destination').text,
        'DepartureTimeStamp': xml_flight.find('./DepartureTimeStamp').text,
        'ArrivalTimeStamp': xml_flight.find('./ArrivalTimeStamp').text,
        'Class': xml_flight.find('./FlightNumber').text,
        'NumberOfStops': xml_flight.find('./NumberOfStops').text,
        'FareBasis': xml_flight.find('./FareBasis').text.replace('\n', '').replace(' ', ''),
        'WarningText': xml_flight.find('./WarningText').text,
        'TicketType': xml_flight.find('./TicketType').text
    }


def pricing_to_dict(xml_pricing):
    return {
        'currency': xml_pricing.attrib['currency'],
        'ServiceCharges': [
            {
                'type': i.attrib['type'],
                'ChargeType': i.attrib['ChargeType'],
                'value': float(i.text)
            }
            for i in xml_pricing
        ]
    }


def parse_xml_flights(filename):
    xml_object = ElementTree.parse(filename).getroot()

    flights_list = []

    for flights in xml_object[1]:
        flights_temp = {
            'OnwardPricedItinerary': [flight_xml_to_dict(i) for i in flights.find('./OnwardPricedItinerary/Flights')],
            'Pricing': pricing_to_dict(flights.find('./Pricing'))
        }
        if flights.find('./ReturnPricedItinerary/Flights'):
            flights_temp['ReturnPricedItinerary'] =   [flight_xml_to_dict(i) for i in flights.find('./ReturnPricedItinerary/Flights')]

        flights_list.append(flights_temp)

    return flights_list


def filter_source_destination(flights, source='DXB', destination='BKK'):
    new_flights = []
    for flight in flights:
        onward = flight['OnwardPricedItinerary']
        source_ok = False
        destination_ok = False
        for flight_1 in onward:
            if flight_1['Source'] == source:
                source_ok = True
            if flight_1['Destination'] == destination:
                destination_ok = True
        if not (source_ok and destination_ok):
            continue

        return_flights = flight.get('ReturnPricedItinerary')
        if return_flights:
            source_ok = False
            destination_ok = False
            for flight_1 in return_flights:
                if flight_1['Source'] == destination:
                    source_ok = True
                if flight_1['Destination'] == source:
                    destination_ok = True
            if source_ok and destination_ok:
                new_flights.append(flight)
        else:
            new_flights.append(flight)

    return new_flights


def flight_price(flight_obj):
    return [i['value'] for i in flight_obj['Pricing']['ServiceCharges']
            if i['ChargeType'] == 'TotalAmount' and i['type'] == 'SingleAdult'][0]


def flight_time(flight_obj):
    departure = datetime.strptime(flight_obj[0]['DepartureTimeStamp'], DATETIME_FORMAT)
    arrival = datetime.strptime(flight_obj[-1]['ArrivalTimeStamp'], DATETIME_FORMAT)
    return arrival - departure


def get_info(loc_flight, one_way):
    if one_way:
        time = flight_time(loc_flight['OnwardPricedItinerary'])
    else:
        time = flight_time(loc_flight['OnwardPricedItinerary']) \
                            + flight_time(loc_flight['ReturnPricedItinerary'])
    price = flight_price(loc_flight)

    return time, price


def analyse_min_max_time_price(loc_flights, one_way=False):

    """
    Axioms about flights:
    1. Minimum time flight exist and it is the best when all else parameters are equal with others
    2. Time is competing with price, longer flights should be cheaper. Every hour in flight should decrease flight
    ticket price
    """

    if one_way:
        print('One way')
    else:
        print('With return')
    if one_way:
        sorted_flights = sorted(loc_flights, key=lambda flight: flight_time(flight['OnwardPricedItinerary']))
    else:
        sorted_flights = sorted(loc_flights,
                                key=lambda flight: flight_time(flight['OnwardPricedItinerary'])
                                                   + flight_time(flight['ReturnPricedItinerary'])
                                )
    flight_time_value_fastest, price_value_fastest = get_info(sorted_flights[0], one_way)
    print('Cheapest', 'Time', flight_time_value_fastest, 'Price', price_value_fastest)

    sorted_flights = sorted(loc_flights, key=lambda flight: flight_price(flight))
    flight_time_value_cheapest, price_value_cheapest = get_info(sorted_flights[0], one_way)

    print('Cheapest', 'Time', flight_time_value_cheapest, 'Price', price_value_cheapest)

    # Coefficient means how many SGD costs second in airplane
    time_price_coef = (price_value_fastest-price_value_cheapest)\
                      /(flight_time_value_cheapest.total_seconds()-flight_time_value_fastest.total_seconds())

    print('Time price coef', time_price_coef)
    return time_price_coef


def find_best_flight(loc_flights, one_way, time_price_coef):
    def calculate_rating(flight, min_time):
        # Rating higher worse flight
        loc_time, loc_price = get_info(flight, one_way)
        return loc_price + (loc_time-min_time).total_seconds()*time_price_coef

    if one_way:
        sorted_flights = sorted(loc_flights, key=lambda flight: flight_time(flight['OnwardPricedItinerary']))
    else:
        sorted_flights = sorted(loc_flights,
                                key=lambda flight: flight_time(flight['OnwardPricedItinerary'])
                                                   + flight_time(flight['ReturnPricedItinerary'])
                                )
    flight_time_value_fastest, price_value_fastest = get_info(sorted_flights[0], one_way)
    sorted_flights = sorted(loc_flights, key=lambda flight: calculate_rating(flight, flight_time_value_fastest))
    return sorted_flights[0]
