from dataclasses import dataclass

from dictdiffer import diff
from app.models import Update, clean_station_json
from django.utils.translation import gettext as _


@dataclass
class Change:
    kind: str
    field: str
    field_name: str
    previous: str
    current: str


def get_changes(upd: Update) -> [Change]:
    result = []
    if not upd.previous:
        return result
    clean_station_json(upd.previous)
    clean_station_json(upd.current)
    changes = diff(upd.previous, upd.current)
    for desc, field, change in changes:
        if desc == 'change':
            if isinstance(field, list):
                field = field[0]
            if field in ignore_fields:
                continue
            fn = field.replace('_', ' ').title()
            fva = render_field(field, change[0])
            fvb = render_field(field, change[1])
            result.append(Change('change', field, fn, fva, fvb))

    return result


def render_field(field: str, value: str) -> str:
    if field == 'cards_accepted':
        field_value = ', '.join([LOOKUPS['cards_accepted'].get(v, v) for v in value.split()])
    elif field in LOOKUPS:
        field_value = LOOKUPS[field].get(value, value)
    else:
        field_value = str(value)
    return field_value


ignore_fields = {
    'updated_at',
    'date_last_confirmed',
    'ev_network_ids',
    'beacon_name'
}

LOOKUPS = dict(
    status_code={
        'E': _('Available'),
        'P': _('Planned'),
        'T': _('Temporarily Unavailable'),
    },
    access_detail_code={
        'CALL': _('Call ahead'),
        'KEY_AFTER_HOURS': _('Card key after hours'),
        'KEY_ALWAYS': _('Card key at all times'),
        'CREDIT_CARD_AFTER_HOURS': _('Credit card after hours'),
        'CREDIT_CARD_ALWAYS': _('Credit card at all times'),
        'FLEET': _('Fleet customers only'),
        'GOVERNMENT': _('Government only'),
        'LIMITED_HOURS': _('Limited hours'),
        'RESIDENTIAL': _('Residential'),
    },
    cards_accepted={
        'A': _('American Express'),
        'CREDIT': _('Credit'),
        'Debit': _('Debit'),
        'D': _('Discover'),
        'M': _('MasterCard'),
        'V': _('Visa'),
        'Cash': _('Cash'),
        'Checks': _('Check'),
        'ACCOUNT_BALANCE': _('Account Balance'),
        'ALLIANCE': _('Alliance AutoGas'),
        'ANDROID_PAY': _('Android Pay'),
        'APPLE_PAY': _('Apple Pay'),
        'ARI': _('ARI'),
        'CleanEnergy': _('Clean Energy'),
        'Comdata': _('Comdata'),
        'CFN': _('Commercial Fueling Network'),
        'EFS': _('EFS'),
        'FleetOne': _('Fleet One'),
        'FuelMan': _('Fuelman'),
        'GasCard': _('GASCARD'),
        'PacificPride': _('Pacific Pride'),
        'PHH': _('PHH'),
        'Proprietor': _('Proprietor Fleet Card'),
        'Speedway': _('Speedway'),
        'SuperPass': _('SuperPass'),
        'TCH': _('TCH'),
        'Tchek': _('T-Chek T-Card'),
        'Trillium': _('Trillium'),
        'Voyager': _('Voyager'),
        'Wright_Exp': _('WEX'),
    },
    owner_type_code={
        'FG': _('Federal Government Owned'),
        'J': _('Jointly Owned'),
        'LG': _('Local/Municipal Government Owned'),
        'P': _('Privately Owned'),
        'SG': _('State/Provincial Government Owned'),
        'T': _('Utility Owned'),
    },
    ev_connector_types={
        'NEMA1450': _('NEMA 14-50'),
        'NEMA515': _('NEMA 5-15'),
        'NEMA520': _('NEMA 5-20'),
        'J1772': _('J1772'),
        'J1772COMBO': _('CCS'),
        'CHADEMO': _('CHAdeMO'),
        'TESLA': _('NACS'),
    },
    ev_network={
        '7CHARGE': _('7Charge'),
        'AddÉnergie': _('Technologies 	AddÉnergie'),
        'AMPED_UP': _('AmpedUp! Networks'),
        'AMPUP': _('AmpUp'),
        'BCHYDRO': _('BC Hydro'),
        'Blink Network': _('Blink'),
        'BP_PULSE': _('bp pulse'),
        'CHARGELAB': _('ChargeLab'),
        'ChargePoint Network': _('ChargePoint'),
        'CHARGEUP': _('ChargeUP'),
        'CHARGIE': _('Chargie'),
        'CIRCLE_K': _('CircleK Charge'),
        'COUCHE_TARD': _('CircleK/Couche-Tard Recharge'),
        'Circuit électrique': _('Circuit électrique'),
        'eCharge Network': _('eCharge Network'),
        'Electrify America': _('Electrify America'),
        'Electrify Canada': _('Electrify Canada'),
        'ENVIROSPARK': _('EnviroSpark'),
        'EVCS': _('EV Charging Solutions'),
        'EV': _('Connect 	EV Connect'),
        'EVGATEWAY': _('evGateway'),
        'eVgo Network': _('EVgo'),
        'EVMATCH': _('EVmatch'),
        'EVRANGE': _('EV Range'),
        'FLASH': _('FLASH'),
        'FLO': _('FLO'),
        'FPLEV': _('FPL EVolution'),
        'FCN': _('Francis Energy'),
        'GRAVITI_ENERGY': _('Graviti Energy'),
        'HONEY_BADGER': _('HoneyBadger Charging'),
        'IVY': _('Ivy'),
        'JULE': _('Jule'),
        'LIVINGSTON': _('Livingston Energy Group'),
        'LOOP': _('Loop'),
        'Non-Networked': _('Non-Networked'),
        'NOODOE': _('Noodoe'),
        'OpConnect': _('OpConnect'),
        'PETROCAN': _('Petro-Canada'),
        'POWERFLEX': _('PowerFlex'),
        'POWER_NODE': _('PowerNode'),
        'RED_E': _('Red E Charging'),
        'REVEL': _('Revel'),
        'RIVIAN_ADVENTURE': _('Rivian Adventure Network'),
        'RIVIAN_WAYPOINTS': _('Rivian Waypoints'),
        'SHELL_RECHARGE': _('Shell Recharge'),
        'STAY_N_CHARGE': _('Stay-N-Charge'),
        'Sun': _('Country Highway 	Sun Country Highway'),
        'SWTCH': _('SWTCH Energy'),
        'Tesla Destination': _('Tesla Destination'),
        'Tesla': _('Tesla Supercharger'),
        'UNIVERSAL': _('Universal EV Chargers'),
        'Volta': _('Volta'),
        'WAVE': _('WAVE'),
        'ZEFNET': _('ZEF Network'),
    },
    ev_renewable_source={
        'GEOTHERMAL': _('Geothermal'),
        'HYDRO': _('Hydropower'),
        'LANDFILL': _('Landfill'),
        'LIVESTOCK': _('Livestock Operations'),
        'NONE': _('None'),
        'SOLAR': _('Solar'),
        'WASTEWATER': _('Wastewater Treatment'),
        'WIND': _('Wind'),
    },
    geocode_status={
        'GPS': _('GPS'),
        '200-9': _('Point'),
        '200-8': _('Address'),
        '200-7': _('Intersection'),
        '200-6': _('Street'),
        '200-5': _('Neighborhood'),
        # '200-5': _('Postal Code - Extended'),
        # '200-5': _('Postal Code'),
        '200-4': _('City/Town'),
        '200-3': _('County'),
        '200-2': _('State/Province'),
        '200-1': _('Country'),
        '200-0': _('Unknown'),
    },
    facility_type={
        'AIRPORT': _('Airport'),
        'ARENA': _('Arena'),
        'AUTO_REPAIR': _('Auto Repair Shop'),
        'BANK': _('Bank'),
        'B_AND_B': _('B&B'),
        'BREWERY_DISTILLERY_WINERY': _('Brewery/Distillery/Winery'),
        'CAMPGROUND': _('Campground'),
        'CAR_DEALER': _('Car Dealer'),
        'CARWASH': _('Carwash'),
        'COLLEGE_CAMPUS': _('College Campus'),
        'CONVENIENCE_STORE': _('Convenience Store'),
        'CONVENTION_CENTER': _('Convention Center'),
        'COOP': _('Co-Op'),
        'FACTORY': _('Factory'),
        'FED_GOV': _('Federal Government'),
        'FIRE_STATION': _('Fire Station'),
        'FLEET_GARAGE': _('Fleet Garage'),
        'FUEL_RESELLER': _('Fuel Reseller'),
        'GROCERY': _('Grocery Store'),
        'HARDWARE_STORE': _('Hardware Store'),
        'HOSPITAL': _('Hospital'),
        'HOTEL': _('Hotel'),
        'INN': _('Inn'),
        'LIBRARY': _('Library'),
        'MIL_BASE': _('Military Base'),
        'MOTOR_POOL': _('Motor Pool'),
        'MULTI_UNIT_DWELLING': _('Multi-Family Housing'),
        'MUNI_GOV': _('Municipal Government'),
        'MUSEUM': _('Museum'),
        'NATL_PARK': _('National Park'),
        'OFFICE_BLDG': _('Office Building'),
        'OTHER': _('Other'),
        'OTHER_ENTERTAINMENT': _('Other Entertainment'),
        'PARK': _('Park'),
        'PARKING_GARAGE': _('Parking Garage'),
        'PARKING_LOT': _('Parking Lot'),
        'PAY_GARAGE': _('Pay-Parking Garage'),
        'PAY_LOT': _('Pay-Parking Lot'),
        'PHARMACY': _('Pharmacy'),
        'PLACE_OF_WORSHIP': _('Place of Worship'),
        'PRISON': _('Prison'),
        'PUBLIC': _('Public'),
        'REC_SPORTS_FACILITY': _('Recreational Sports Facility'),
        'REFINERY': _('Refinery'),
        'RENTAL_CAR_RETURN': _('Rental Car Return'),
        'RESEARCH_FACILITY': _('Research Facility/Laboratory'),
        'RESTAURANT': _('Restaurant'),
        'REST_STOP': _('Rest Stop'),
        'RETAIL': _('Retail'),
        'RV_PARK': _('RV Park'),
        'SCHOOL': _('School'),
        'GAS_STATION': _('Service/Gas Station'),
        'SHOPPING_CENTER': _('Shopping Center'),
        'SHOPPING_MALL': _('Shopping Mall'),
        'STADIUM': _('Stadium'),
        'STANDALONE_STATION': _('Standalone Station'),
        'STATE_GOV': _('State/Provincial Government'),
        'STORAGE': _('Storage Facility'),
        'STREET_PARKING': _('Street Parking'),
        'TNC': _('Transportation Network Company'),
        'TRAVEL_CENTER': _('Travel Center'),
        'TRUCK_STOP': _('Truck Stop'),
        'UTILITY': _('Utility'),
        'WORKPLACE': _('Workplace'),
    },
    maximum_vehicle_class={
        'LD': _('Passenger vehicles (class 1-2)'),
        'MD': _('Medium-duty (class 3-5)'),
        'HD': _('Heavy-duty (class 6-8)'),
    }
)
