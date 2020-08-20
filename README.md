# ops2fhir

Python script to transform OPS data into FHIR format.

## Info
* This is a minimal standalone script to showcase how to transform data from the German Procedure Classification (Operationen- und Prozedurenschlüssel – OPS) to FHIR format as specified by the [Medical Informatics-Initiative (MII)](https://www.medizininformatik-initiative.de/). The underlying mapping of OPS codes to Identification of Medicinal Products (IDMP) compliant terminology is based on the publication *S. Zabka, D. Ammon, T. Ganslandt, J. Gewehr, C. Haverkamp, S. Kiefer, H. Lautenbacher, M. Löbe, S. Thun, and M. Boeker, Towards a Medication Core Data Set for the Medical Informatics Initiative (MII): Initial Mapping Experience between the German Procedure Classification (OPS) and the Identification of Medicinal Products (IDMP). In CEUR Workshop Proceedings.*

## Prerequisites
* Python 3.X
* SMART on FHIR Python client
* Pandas

## Installation
* To install the FHIR Python client in your environment use: 
`pip install git+git://github.com/smart-on-fhir/client-py.git`

* Install the pandas library via:
`pip install pandas`

* Clone the repository:
`git clone https://github.com/julsas/ops2fhir.git`

## Usage
* Run ops2fhir.py
* You will be prompted to specify the URL of your FHIR server
* The script will transform the given example mapping to FHIR and send the resources to the server

## License
* [MIT](https://tldrlegal.com/license/mit-license)

## Links
* [FHIR profiles from the Medical Informatics Initiative (MII)](https://simplifier.net/organization/koordinationsstellemii)
* [SMART on FHIR Python Client](http://docs.smarthealthit.org/client-py/index.html)