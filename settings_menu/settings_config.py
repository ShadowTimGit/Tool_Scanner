DEFAULT_SAE_SIZES = [
    "NA",
    "1/4\"",
    "9/32\"",
    "5/16\"",
    "11/32\"",
    "3/8\"",
    "7/16\"",
    "1/2\"",
    "9/16\"",
    "5/8\"",
    "11/16\"",
    "3/4\"",
    "13/16\"",
    "7/8\"",
    "15/16\"",
    "1\"",
    "1-1/16\"",
    "1-1/8\"",
    "1-3/16\"",
    "1-1/4\"",
    "1-5/16\"",
    "1-3/8\"",
    "1-7/16\"",
    "1-1/2\"",
]


DEFAULT_METRIC_SIZES = [
    "NA",
    "6mm",
    "7mm",
    "8mm",
    "9mm",
    "10mm",
    "11mm",
    "12mm",
    "13mm",
    "14mm",
    "15mm",
    "16mm",
    "17mm",
    "18mm",
    "19mm",
    "20mm",
    "21mm",
    "22mm",
    "23mm",
    "24mm",
    "25mm",
    "26mm",
    "27mm",
    "28mm",
    "29mm",
    "30mm",
    "32mm",
    "34mm",
    "36mm",
    "38mm",
    "40mm",
    "41mm",
    "42mm",
    "46mm",
    "50mm",
]

DEFAULT_OTHER = [
    "NA",
    "Other",
    "Adjustable",
    "Awl",
    "Brake tool",
    "Flathead",
    "#2 Philips",
    "Philips",
    "Needle Nose",
    "Pick",
    "Specialty",
    "T15H",
    "T20",
    "T25",
    "T27",
    "T27H",
    "T45",
    "T47",
    "T50",
]

DEFAULT_SIZE = "1/4"

DEFAULT_SPECIALTY_SOCKET = [
    "N/A",
    "No",
    "Yes",
]


DEFAULT_DRIVE = [
    "N/A",
    "1/4\"",
    "3/8\"",
    "1/2\"",
    "3/4\"",
    "1\"",
    "1-1/2\"",
    "2-1/2\"",
]


DEFAULT_POINT = [
    "N/A",
    "6 Point",
    "8 Point",
    "10 Point",
    "12 Point",
    "16 Point",
    "18 Point",
    "24 Point",
    "Torx",
    "Torx Security",
    "Hex",
    "Hex Security",
    "Spline",
    "Triple Square",
    "Ribe",
    "XZN",
]


DEFAULT_METADATA = {
    "sizes": {
        "SAE": DEFAULT_SAE_SIZES,
        "Metric": DEFAULT_METRIC_SIZES,
        "Other": DEFAULT_OTHER,
    },
    "drive": DEFAULT_DRIVE,
    "point": DEFAULT_POINT,
    "specialty_socket": DEFAULT_SPECIALTY_SOCKET,
}