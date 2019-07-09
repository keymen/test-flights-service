from helpers import parse_xml_flights, filter_source_destination, DATETIME_FORMAT, analyse_min_max_time_price
from datetime import datetime


class FlightDirectionException(Exception):
    pass


class FlightTimeException(Exception):
    pass


class FlightSourceArrivalException(Exception):
    pass


class FlightOrderException(Exception):
    pass


class InvalidCurrency(Exception):
    pass


def check_direction(flights, is_one_way=False):
    # In the problem we consider that one file includes only one way flights and another one only flights with return
    for flight in flights:
        if is_one_way:
            if 'OnwardPricedItinerary' not in flight.keys():
                raise FlightDirectionException
            if 'ReturnPricedItinerary' in flight.keys():
                raise FlightDirectionException
        else:
            if ('OnwardPricedItinerary', 'ReturnPricedItinerary') in flight.keys():
                raise FlightDirectionException


def check_source_arrive(flights, source='DXB', destination='BKK'):
    # In the problem we consider that onward flights from BKK to DXB and return from DXB to BKK
    # It is not true
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
            raise FlightDirectionException

        return_flights = flight.get('ReturnPricedItinerary')
        if return_flights:
            source_ok = False
            destination_ok = False
            for flight_1 in return_flights:
                if flight_1['Source'] == destination:
                    source_ok = True
                if flight_1['Destination'] == source:
                    destination_ok = True
            if not (source_ok and destination_ok):
                raise FlightDirectionException


def check_flight_order(flights):
    # In the problem we consider that flights order is right and departure time after arrival for every flight

    def check_order(flights_objs):
        flights_num = len(flights_objs)
        if flights_num == 1:
            return
        for i in range(flights_num - 1):
            if flights_objs[i]['Destination'] != flights_objs[i+1]['Source']:
                raise FlightOrderException
            arrival_time = datetime.strptime(flights_objs[i]['ArrivalTimeStamp'], DATETIME_FORMAT)
            departure_time = datetime.strptime(flights_objs[i+1]['DepartureTimeStamp'], DATETIME_FORMAT)
            if arrival_time > departure_time:
                raise FlightTimeException

    for flight in flights:
        onward = flight['OnwardPricedItinerary']
        check_order(onward)
        return_flights = flight.get('ReturnPricedItinerary')
        if return_flights:
            check_order(return_flights)


def check_all_currency_sgd(flights):
    # In the problem we consider that price currency of all flights is SGD
    for flight in flights:
        if flight['Pricing']['currency'] != 'SGD':
            raise InvalidCurrency


if __name__ == '__main__':
    flights_one_way = parse_xml_flights('search_responses/RS_ViaOW.xml')
    flights_with_return = parse_xml_flights('search_responses/RS_Via-3.xml')

    # First of all filter irrelevant flights
    flights_one_way = filter_source_destination(flights_one_way)
    flights_with_return = filter_source_destination(flights_with_return)

    check_direction(flights_one_way, True)
    check_direction(flights_with_return)

    check_source_arrive(flights_one_way)
    check_source_arrive(flights_with_return)

    check_flight_order(flights_one_way)
    check_flight_order(flights_with_return)

    check_all_currency_sgd(flights_one_way)
    check_all_currency_sgd(flights_with_return)

    analyse_min_max_time_price(flights_one_way, True)
    analyse_min_max_time_price(flights_with_return)
