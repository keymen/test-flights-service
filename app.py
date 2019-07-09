from flask import Flask, request, jsonify
from helpers import parse_xml_flights, flight_price, flight_time, filter_source_destination, analyse_min_max_time_price, \
    find_best_flight

app = Flask(__name__)
flights_one_way = parse_xml_flights('search_responses/RS_ViaOW.xml')
flights_with_return = parse_xml_flights('search_responses/RS_Via-3.xml')
flights_one_way = filter_source_destination(flights_one_way)
flights_with_return = filter_source_destination(flights_with_return)
time_price_coef_one_way = analyse_min_max_time_price(flights_one_way, True)
time_price_coef_with_return = analyse_min_max_time_price(flights_with_return)


@app.route('/dxb_bkk_options', methods=['GET'])
def dxb_bkk_options():
    one_way = True if request.args.get('one_way') == 'true' else False
    if one_way:
        return jsonify(flights_one_way)
    return jsonify(flights_with_return)


@app.route('/dxb_bkk_routes', methods=['GET'])
def dxb_bkk_routes():
    one_way = True if request.args.get('one_way') == 'true' else False
    cheapest = True if request.args.get('cheapest') == 'true' else False
    fastest = True if request.args.get('fastest') == 'true' else False
    best = True if request.args.get('best') == 'true' else False

    if one_way:
        loc_flights = flights_one_way
    else:
        loc_flights = flights_with_return

    if cheapest:
        sorted_flights = sorted(loc_flights, key=lambda flight: flight_price(flight))
        return jsonify(sorted_flights[0])

    if fastest:
        if one_way:
            sorted_flights = sorted(loc_flights, key=lambda flight: flight_time(flight['OnwardPricedItinerary']))
        else:
            sorted_flights = sorted(loc_flights,
                                    key=lambda flight: flight_time(flight['OnwardPricedItinerary'])
                                                       + flight_time(flight['ReturnPricedItinerary'])
                                    )
        return jsonify(sorted_flights[0])
    if best:
        if one_way:
            time_price_coef = time_price_coef_one_way
        else:
            time_price_coef = time_price_coef_with_return
        best_flight = find_best_flight(loc_flights, one_way, time_price_coef)
        return jsonify(best_flight)

    return jsonify({})


if __name__ == '__main__':
    app.run()
