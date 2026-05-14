# Synthea FHIR Profile

## Notes on Synthea data characteristics

- **Terminology**: Synthea uses SNOMED CT (8-digit SCTIDs) as its primary clinical
  vocabulary for Condition and Procedure resources. This aligns with the Australian
  Digital Health Agency standard. If/when US claims data is ingested, a
  SNOMED-to-ICD-10-CM crosswalk dimension is required.
- **Hospitalization sub-resource**: only populated on ~0.1% of Encounter records
  (true inpatient admissions). Readmission identification therefore derives from
  `class.code IN ('IMP', 'EMER')` plus `period.start`/`period.end`, not from
  `hospitalization.admitSource`/`dischargeDisposition`.

## AllergyIntolerance
**Bronze plan**: bronzed

- Source file: `AllergyIntolerance.ndjson`
- Total records: 10468
- Sample size: 1000

### Schema Presence
- `category`: 100.0%
- `category[]`: 100.0%
- `clinicalStatus`: 100.0%
- `clinicalStatus.coding`: 100.0%
- `clinicalStatus.coding[]`: 100.0%
- `clinicalStatus.coding[].code`: 100.0%
- `clinicalStatus.coding[].system`: 100.0%
- `code`: 100.0%
- `code.coding`: 100.0%
- `code.coding[]`: 100.0%
- `code.coding[].code`: 100.0%
- `code.coding[].display`: 100.0%
- `code.coding[].system`: 100.0%
- `code.text`: 100.0%
- `criticality`: 100.0%
- `id`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `patient`: 100.0%
- `patient.reference`: 100.0%
- `reaction`: 42.5%
- `reaction[]`: 42.5%
- `reaction[].manifestation`: 42.5%
- `reaction[].manifestation[]`: 42.5%
- `reaction[].manifestation[].coding`: 42.5%
- `reaction[].manifestation[].coding[]`: 42.5%
- `reaction[].manifestation[].coding[].code`: 42.5%
- `reaction[].manifestation[].coding[].display`: 42.5%
- `reaction[].manifestation[].coding[].system`: 42.5%
- `reaction[].manifestation[].text`: 42.5%
- `reaction[].severity`: 38.7%
- `recordedDate`: 100.0%
- `resourceType`: 100.0%
- `type`: 100.0%
- `verificationStatus`: 100.0%
- `verificationStatus.coding`: 100.0%
- `verificationStatus.coding[]`: 100.0%
- `verificationStatus.coding[].code`: 100.0%
- `verificationStatus.coding[].system`: 100.0%

## CarePlan
**Bronze plan**: bronzed

- Source file: `CarePlan.ndjson`
- Total records: 37736
- Sample size: 1000

### Schema Presence
- `activity`: 98.4%
- `activity[]`: 98.4%
- `activity[].detail`: 98.4%
- `activity[].detail.code`: 98.4%
- `activity[].detail.code.coding`: 98.4%
- `activity[].detail.code.coding[]`: 98.4%
- `activity[].detail.code.coding[].code`: 98.4%
- `activity[].detail.code.coding[].display`: 98.4%
- `activity[].detail.code.coding[].system`: 98.4%
- `activity[].detail.code.text`: 98.4%
- `activity[].detail.location`: 98.4%
- `activity[].detail.location.display`: 98.4%
- `activity[].detail.reasonCode`: 0.9%
- `activity[].detail.reasonCode[]`: 0.9%
- `activity[].detail.reasonCode[].coding`: 0.9%
- `activity[].detail.reasonCode[].coding[]`: 0.9%
- `activity[].detail.reasonCode[].coding[].code`: 0.9%
- `activity[].detail.reasonCode[].coding[].display`: 0.9%
- `activity[].detail.reasonCode[].coding[].system`: 0.9%
- `activity[].detail.reasonCode[].text`: 0.9%
- `activity[].detail.reasonReference`: 47.2%
- `activity[].detail.reasonReference[]`: 47.2%
- `activity[].detail.reasonReference[].reference`: 47.2%
- `activity[].detail.status`: 98.4%
- `addresses`: 47.4%
- `addresses[]`: 47.4%
- `addresses[].reference`: 47.4%
- `careTeam`: 100.0%
- `careTeam[]`: 100.0%
- `careTeam[].reference`: 100.0%
- `category`: 100.0%
- `category[]`: 100.0%
- `category[].coding`: 100.0%
- `category[].coding[]`: 100.0%
- `category[].coding[].code`: 100.0%
- `category[].coding[].display`: 100.0%
- `category[].coding[].system`: 100.0%
- `category[].text`: 100.0%
- `encounter`: 100.0%
- `encounter.reference`: 100.0%
- `id`: 100.0%
- `intent`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `period`: 100.0%
- `period.end`: 53.2%
- `period.start`: 100.0%
- `resourceType`: 100.0%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%
- `text`: 100.0%
- `text.div`: 100.0%
- `text.status`: 100.0%

## CareTeam
**Bronze plan**: bronzed

- Source file: `CareTeam.ndjson`
- Total records: 37736
- Sample size: 1000

### Schema Presence
- `encounter`: 100.0%
- `encounter.reference`: 100.0%
- `id`: 100.0%
- `managingOrganization`: 100.0%
- `managingOrganization[]`: 100.0%
- `managingOrganization[].display`: 100.0%
- `managingOrganization[].reference`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `participant`: 100.0%
- `participant[]`: 100.0%
- `participant[].member`: 100.0%
- `participant[].member.display`: 100.0%
- `participant[].member.reference`: 100.0%
- `participant[].role`: 100.0%
- `participant[].role[]`: 100.0%
- `participant[].role[].coding`: 100.0%
- `participant[].role[].coding[]`: 100.0%
- `participant[].role[].coding[].code`: 100.0%
- `participant[].role[].coding[].display`: 100.0%
- `participant[].role[].coding[].system`: 100.0%
- `participant[].role[].text`: 100.0%
- `period`: 100.0%
- `period.end`: 53.2%
- `period.start`: 100.0%
- `reasonCode`: 48.3%
- `reasonCode[]`: 48.3%
- `reasonCode[].coding`: 48.3%
- `reasonCode[].coding[]`: 48.3%
- `reasonCode[].coding[].code`: 48.3%
- `reasonCode[].coding[].display`: 48.3%
- `reasonCode[].coding[].system`: 48.3%
- `reasonCode[].text`: 48.3%
- `resourceType`: 100.0%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%

## Claim
**Bronze plan**: bronzed

- Source file: `Claim.ndjson`
- Total records: 1237848
- Sample size: 1000

### Schema Presence
- `billablePeriod`: 100.0%
- `billablePeriod.end`: 100.0%
- `billablePeriod.start`: 100.0%
- `created`: 100.0%
- `diagnosis`: 32.7%
- `diagnosis[]`: 32.7%
- `diagnosis[].diagnosisReference`: 32.7%
- `diagnosis[].diagnosisReference.reference`: 32.7%
- `diagnosis[].sequence`: 32.7%
- `facility`: 61.8%
- `facility.display`: 61.8%
- `facility.reference`: 61.8%
- `id`: 100.0%
- `insurance`: 100.0%
- `insurance[]`: 100.0%
- `insurance[].coverage`: 100.0%
- `insurance[].coverage.display`: 100.0%
- `insurance[].focal`: 100.0%
- `insurance[].sequence`: 100.0%
- `item`: 100.0%
- `item[]`: 100.0%
- `item[].diagnosisSequence`: 32.7%
- `item[].diagnosisSequence[]`: 32.7%
- `item[].encounter`: 100.0%
- `item[].encounter[]`: 100.0%
- `item[].encounter[].reference`: 100.0%
- `item[].informationSequence`: 30.4%
- `item[].informationSequence[]`: 30.4%
- `item[].net`: 46.0%
- `item[].net.currency`: 46.0%
- `item[].net.value`: 46.0%
- `item[].procedureSequence`: 38.1%
- `item[].procedureSequence[]`: 38.1%
- `item[].productOrService`: 100.0%
- `item[].productOrService.coding`: 100.0%
- `item[].productOrService.coding[]`: 100.0%
- `item[].productOrService.coding[].code`: 100.0%
- `item[].productOrService.coding[].display`: 100.0%
- `item[].productOrService.coding[].system`: 100.0%
- `item[].productOrService.text`: 100.0%
- `item[].sequence`: 100.0%
- `patient`: 100.0%
- `patient.display`: 61.8%
- `patient.reference`: 100.0%
- `prescription`: 38.2%
- `prescription.reference`: 38.2%
- `priority`: 100.0%
- `priority.coding`: 100.0%
- `priority.coding[]`: 100.0%
- `priority.coding[].code`: 100.0%
- `priority.coding[].system`: 100.0%
- `procedure`: 38.1%
- `procedure[]`: 38.1%
- `procedure[].procedureReference`: 38.1%
- `procedure[].procedureReference.reference`: 38.1%
- `procedure[].sequence`: 38.1%
- `provider`: 100.0%
- `provider.display`: 100.0%
- `provider.reference`: 100.0%
- `resourceType`: 100.0%
- `status`: 100.0%
- `supportingInfo`: 30.4%
- `supportingInfo[]`: 30.4%
- `supportingInfo[].category`: 30.4%
- `supportingInfo[].category.coding`: 30.4%
- `supportingInfo[].category.coding[]`: 30.4%
- `supportingInfo[].category.coding[].code`: 30.4%
- `supportingInfo[].category.coding[].system`: 30.4%
- `supportingInfo[].sequence`: 30.4%
- `supportingInfo[].valueReference`: 17.8%
- `supportingInfo[].valueReference.reference`: 17.8%
- `total`: 100.0%
- `total.currency`: 100.0%
- `total.value`: 100.0%
- `type`: 100.0%
- `type.coding`: 100.0%
- `type.coding[]`: 100.0%
- `type.coding[].code`: 100.0%
- `type.coding[].system`: 100.0%
- `use`: 100.0%

## Condition
**Bronze plan**: bronzed

- Source file: `Condition.ndjson`
- Total records: 412692
- Sample size: 1000

### Schema Presence
- `abatementDateTime`: 71.8%
- `category`: 100.0%
- `category[]`: 100.0%
- `category[].coding`: 100.0%
- `category[].coding[]`: 100.0%
- `category[].coding[].code`: 100.0%
- `category[].coding[].display`: 100.0%
- `category[].coding[].system`: 100.0%
- `clinicalStatus`: 100.0%
- `clinicalStatus.coding`: 100.0%
- `clinicalStatus.coding[]`: 100.0%
- `clinicalStatus.coding[].code`: 100.0%
- `clinicalStatus.coding[].system`: 100.0%
- `code`: 100.0%
- `code.coding`: 100.0%
- `code.coding[]`: 100.0%
- `code.coding[].code`: 100.0%
- `code.coding[].display`: 100.0%
- `code.coding[].system`: 100.0%
- `code.text`: 100.0%
- `encounter`: 100.0%
- `encounter.reference`: 100.0%
- `id`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `onsetDateTime`: 100.0%
- `recordedDate`: 100.0%
- `resourceType`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%
- `verificationStatus`: 100.0%
- `verificationStatus.coding`: 100.0%
- `verificationStatus.coding[]`: 100.0%
- `verificationStatus.coding[].code`: 100.0%
- `verificationStatus.coding[].system`: 100.0%

### Condition Stats
- `314529007` (Medication review due (situation)): 191
- `160903007` (Full-time employment (finding)): 74
- `66383009` (Gingivitis (disorder)): 70
- `73595000` (Stress (finding)): 68
- `160904001` (Part-time employment (finding)): 43
- `444814009` (Viral sinusitis (disorder)): 33
- `422650009` (Social isolation (finding)): 30
- `224299000` (Received higher education (finding)): 25
- `423315002` (Limited social contact (finding)): 22
- `18718003` (Gingival disease (disorder)): 22

## Device
**Bronze plan**: available-not-bronzed

- Source file: `Device.ndjson`
- Total records: 65239
- Sample size: 1000

### Schema Presence
- `deviceName`: 100.0%
- `deviceName[]`: 100.0%
- `deviceName[].name`: 100.0%
- `deviceName[].type`: 100.0%
- `distinctIdentifier`: 100.0%
- `expirationDate`: 100.0%
- `id`: 100.0%
- `lotNumber`: 100.0%
- `manufactureDate`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `patient`: 100.0%
- `patient.reference`: 100.0%
- `resourceType`: 100.0%
- `serialNumber`: 100.0%
- `status`: 100.0%
- `type`: 100.0%
- `type.coding`: 100.0%
- `type.coding[]`: 100.0%
- `type.coding[].code`: 100.0%
- `type.coding[].display`: 100.0%
- `type.coding[].system`: 100.0%
- `type.text`: 100.0%
- `udiCarrier`: 100.0%
- `udiCarrier[]`: 100.0%
- `udiCarrier[].carrierHRF`: 100.0%
- `udiCarrier[].deviceIdentifier`: 100.0%

## DiagnosticReport
**Bronze plan**: available-not-bronzed

- Source file: `DiagnosticReport.ndjson`
- Total records: 1323152
- Sample size: 1000

### Schema Presence
- `category`: 74.3%
- `category[]`: 74.3%
- `category[].coding`: 74.3%
- `category[].coding[]`: 74.3%
- `category[].coding[].code`: 74.3%
- `category[].coding[].display`: 74.3%
- `category[].coding[].system`: 74.3%
- `code`: 100.0%
- `code.coding`: 100.0%
- `code.coding[]`: 100.0%
- `code.coding[].code`: 100.0%
- `code.coding[].display`: 100.0%
- `code.coding[].system`: 100.0%
- `code.text`: 39.6%
- `effectiveDateTime`: 100.0%
- `encounter`: 100.0%
- `encounter.reference`: 100.0%
- `id`: 100.0%
- `issued`: 100.0%
- `meta`: 74.3%
- `meta.profile`: 74.3%
- `meta.profile[]`: 74.3%
- `performer`: 74.3%
- `performer[]`: 74.3%
- `performer[].display`: 74.3%
- `performer[].reference`: 74.3%
- `presentedForm`: 60.4%
- `presentedForm[]`: 60.4%
- `presentedForm[].contentType`: 60.4%
- `presentedForm[].data`: 60.4%
- `resourceType`: 100.0%
- `result`: 39.6%
- `result[]`: 39.6%
- `result[].display`: 39.6%
- `result[].reference`: 39.6%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%

## DocumentReference
**Bronze plan**: bronzed

- Source file: `DocumentReference.ndjson`
- Total records: 664623
- Sample size: 1000

### Schema Presence
- `author`: 100.0%
- `author[]`: 100.0%
- `author[].display`: 100.0%
- `author[].reference`: 100.0%
- `category`: 100.0%
- `category[]`: 100.0%
- `category[].coding`: 100.0%
- `category[].coding[]`: 100.0%
- `category[].coding[].code`: 100.0%
- `category[].coding[].display`: 100.0%
- `category[].coding[].system`: 100.0%
- `content`: 100.0%
- `content[]`: 100.0%
- `content[].attachment`: 100.0%
- `content[].attachment.contentType`: 100.0%
- `content[].attachment.data`: 100.0%
- `content[].format`: 100.0%
- `content[].format.code`: 100.0%
- `content[].format.display`: 100.0%
- `content[].format.system`: 100.0%
- `context`: 100.0%
- `context.encounter`: 100.0%
- `context.encounter[]`: 100.0%
- `context.encounter[].reference`: 100.0%
- `context.period`: 100.0%
- `context.period.end`: 100.0%
- `context.period.start`: 100.0%
- `custodian`: 100.0%
- `custodian.display`: 100.0%
- `custodian.reference`: 100.0%
- `date`: 100.0%
- `id`: 100.0%
- `identifier`: 100.0%
- `identifier[]`: 100.0%
- `identifier[].system`: 100.0%
- `identifier[].value`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `resourceType`: 100.0%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%
- `type`: 100.0%
- `type.coding`: 100.0%
- `type.coding[]`: 100.0%
- `type.coding[].code`: 100.0%
- `type.coding[].display`: 100.0%
- `type.coding[].system`: 100.0%

## Encounter
**Bronze plan**: bronzed

- Source file: `Encounter.ndjson`
- Total records: 664623
- Sample size: 1000

### Schema Presence
- `class`: 100.0%
- `class.code`: 100.0%
- `class.system`: 100.0%
- `hospitalization`: 0.1%
- `hospitalization.dischargeDisposition`: 0.1%
- `hospitalization.dischargeDisposition.coding`: 0.1%
- `hospitalization.dischargeDisposition.coding[]`: 0.1%
- `hospitalization.dischargeDisposition.coding[].code`: 0.1%
- `hospitalization.dischargeDisposition.coding[].display`: 0.1%
- `hospitalization.dischargeDisposition.coding[].system`: 0.1%
- `hospitalization.dischargeDisposition.text`: 0.1%
- `id`: 100.0%
- `identifier`: 100.0%
- `identifier[]`: 100.0%
- `identifier[].system`: 100.0%
- `identifier[].use`: 100.0%
- `identifier[].value`: 100.0%
- `location`: 100.0%
- `location[]`: 100.0%
- `location[].location`: 100.0%
- `location[].location.display`: 100.0%
- `location[].location.reference`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `participant`: 100.0%
- `participant[]`: 100.0%
- `participant[].individual`: 100.0%
- `participant[].individual.display`: 100.0%
- `participant[].individual.reference`: 100.0%
- `participant[].period`: 100.0%
- `participant[].period.end`: 100.0%
- `participant[].period.start`: 100.0%
- `participant[].type`: 100.0%
- `participant[].type[]`: 100.0%
- `participant[].type[].coding`: 100.0%
- `participant[].type[].coding[]`: 100.0%
- `participant[].type[].coding[].code`: 100.0%
- `participant[].type[].coding[].display`: 100.0%
- `participant[].type[].coding[].system`: 100.0%
- `participant[].type[].text`: 100.0%
- `period`: 100.0%
- `period.end`: 100.0%
- `period.start`: 100.0%
- `reasonCode`: 59.7%
- `reasonCode[]`: 59.7%
- `reasonCode[].coding`: 59.7%
- `reasonCode[].coding[]`: 59.7%
- `reasonCode[].coding[].code`: 59.7%
- `reasonCode[].coding[].display`: 59.7%
- `reasonCode[].coding[].system`: 59.7%
- `resourceType`: 100.0%
- `serviceProvider`: 100.0%
- `serviceProvider.display`: 100.0%
- `serviceProvider.reference`: 100.0%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.display`: 100.0%
- `subject.reference`: 100.0%
- `type`: 100.0%
- `type[]`: 100.0%
- `type[].coding`: 100.0%
- `type[].coding[]`: 100.0%
- `type[].coding[].code`: 100.0%
- `type[].coding[].display`: 100.0%
- `type[].coding[].system`: 100.0%
- `type[].text`: 100.0%

### Encounter Stats
- Class distribution:
  - AMB: 957
  - EMER: 31
  - HH: 1
  - IMP: 8
  - VR: 3
- Status distribution:
  - finished: 1000
- Period start min: 1928-08-20T13:03:18Z
- Period start max: 2026-05-09T10:21:10Z
- Period start median: 2018-11-30T06:34:59.500000Z
- Period end min: 1928-08-20T13:18:18Z
- Period end max: 2026-05-09T11:00:00Z
- Period end median: 2018-11-30T06:57:52.500000Z

## ExplanationOfBenefit
**Bronze plan**: available-not-bronzed

- Source file: `ExplanationOfBenefit.ndjson`
- Total records: 1237848
- Sample size: 1000

### Schema Presence
- `billablePeriod`: 100.0%
- `billablePeriod.end`: 100.0%
- `billablePeriod.start`: 100.0%
- `careTeam`: 100.0%
- `careTeam[]`: 100.0%
- `careTeam[].provider`: 100.0%
- `careTeam[].provider.reference`: 100.0%
- `careTeam[].role`: 100.0%
- `careTeam[].role.coding`: 100.0%
- `careTeam[].role.coding[]`: 100.0%
- `careTeam[].role.coding[].code`: 100.0%
- `careTeam[].role.coding[].display`: 100.0%
- `careTeam[].role.coding[].system`: 100.0%
- `careTeam[].sequence`: 100.0%
- `claim`: 100.0%
- `claim.reference`: 100.0%
- `contained`: 100.0%
- `contained[]`: 100.0%
- `contained[].beneficiary`: 100.0%
- `contained[].beneficiary.reference`: 100.0%
- `contained[].id`: 100.0%
- `contained[].intent`: 100.0%
- `contained[].payor`: 100.0%
- `contained[].payor[]`: 100.0%
- `contained[].payor[].display`: 100.0%
- `contained[].performer`: 100.0%
- `contained[].performer[]`: 100.0%
- `contained[].performer[].reference`: 100.0%
- `contained[].requester`: 100.0%
- `contained[].requester.reference`: 100.0%
- `contained[].resourceType`: 100.0%
- `contained[].status`: 100.0%
- `contained[].subject`: 100.0%
- `contained[].subject.reference`: 100.0%
- `contained[].type`: 100.0%
- `contained[].type.text`: 100.0%
- `created`: 100.0%
- `diagnosis`: 32.7%
- `diagnosis[]`: 32.7%
- `diagnosis[].diagnosisReference`: 32.7%
- `diagnosis[].diagnosisReference.reference`: 32.7%
- `diagnosis[].sequence`: 32.7%
- `diagnosis[].type`: 32.7%
- `diagnosis[].type[]`: 32.7%
- `diagnosis[].type[].coding`: 32.7%
- `diagnosis[].type[].coding[]`: 32.7%
- `diagnosis[].type[].coding[].code`: 32.7%
- `diagnosis[].type[].coding[].system`: 32.7%
- `facility`: 100.0%
- `facility.display`: 100.0%
- `facility.reference`: 100.0%
- `id`: 100.0%
- `identifier`: 100.0%
- `identifier[]`: 100.0%
- `identifier[].system`: 100.0%
- `identifier[].value`: 100.0%
- `insurance`: 100.0%
- `insurance[]`: 100.0%
- `insurance[].coverage`: 100.0%
- `insurance[].coverage.display`: 100.0%
- `insurance[].coverage.reference`: 100.0%
- `insurance[].focal`: 100.0%
- `insurer`: 100.0%
- `insurer.display`: 100.0%
- `item`: 100.0%
- `item[]`: 100.0%
- `item[].adjudication`: 46.0%
- `item[].adjudication[]`: 46.0%
- `item[].adjudication[].amount`: 46.0%
- `item[].adjudication[].amount.currency`: 46.0%
- `item[].adjudication[].amount.value`: 46.0%
- `item[].adjudication[].category`: 46.0%
- `item[].adjudication[].category.coding`: 46.0%
- `item[].adjudication[].category.coding[]`: 46.0%
- `item[].adjudication[].category.coding[].code`: 46.0%
- `item[].adjudication[].category.coding[].display`: 46.0%
- `item[].adjudication[].category.coding[].system`: 46.0%
- `item[].category`: 100.0%
- `item[].category.coding`: 100.0%
- `item[].category.coding[]`: 100.0%
- `item[].category.coding[].code`: 100.0%
- `item[].category.coding[].display`: 100.0%
- `item[].category.coding[].system`: 100.0%
- `item[].diagnosisSequence`: 32.7%
- `item[].diagnosisSequence[]`: 32.7%
- `item[].encounter`: 100.0%
- `item[].encounter[]`: 100.0%
- `item[].encounter[].reference`: 100.0%
- `item[].informationSequence`: 30.4%
- `item[].informationSequence[]`: 30.4%
- `item[].locationCodeableConcept`: 100.0%
- `item[].locationCodeableConcept.coding`: 100.0%
- `item[].locationCodeableConcept.coding[]`: 100.0%
- `item[].locationCodeableConcept.coding[].code`: 100.0%
- `item[].locationCodeableConcept.coding[].display`: 100.0%
- `item[].locationCodeableConcept.coding[].system`: 100.0%
- `item[].net`: 46.0%
- `item[].net.currency`: 46.0%
- `item[].net.value`: 46.0%
- `item[].productOrService`: 100.0%
- `item[].productOrService.coding`: 100.0%
- `item[].productOrService.coding[]`: 100.0%
- `item[].productOrService.coding[].code`: 100.0%
- `item[].productOrService.coding[].display`: 100.0%
- `item[].productOrService.coding[].system`: 100.0%
- `item[].productOrService.text`: 100.0%
- `item[].sequence`: 100.0%
- `item[].servicedPeriod`: 100.0%
- `item[].servicedPeriod.end`: 100.0%
- `item[].servicedPeriod.start`: 100.0%
- `outcome`: 100.0%
- `patient`: 100.0%
- `patient.reference`: 100.0%
- `payment`: 100.0%
- `payment.amount`: 100.0%
- `payment.amount.currency`: 100.0%
- `payment.amount.value`: 100.0%
- `provider`: 100.0%
- `provider.reference`: 100.0%
- `referral`: 100.0%
- `referral.reference`: 100.0%
- `resourceType`: 100.0%
- `status`: 100.0%
- `total`: 100.0%
- `total[]`: 100.0%
- `total[].amount`: 100.0%
- `total[].amount.currency`: 100.0%
- `total[].amount.value`: 100.0%
- `total[].category`: 100.0%
- `total[].category.coding`: 100.0%
- `total[].category.coding[]`: 100.0%
- `total[].category.coding[].code`: 100.0%
- `total[].category.coding[].display`: 100.0%
- `total[].category.coding[].system`: 100.0%
- `total[].category.text`: 100.0%
- `type`: 100.0%
- `type.coding`: 100.0%
- `type.coding[]`: 100.0%
- `type.coding[].code`: 100.0%
- `type.coding[].system`: 100.0%
- `use`: 100.0%

## ImagingStudy
**Bronze plan**: available-not-bronzed

- Source file: `ImagingStudy.ndjson`
- Total records: 52673
- Sample size: 1000

### Schema Presence
- `encounter`: 100.0%
- `encounter.reference`: 100.0%
- `id`: 100.0%
- `identifier`: 100.0%
- `identifier[]`: 100.0%
- `identifier[].system`: 100.0%
- `identifier[].use`: 100.0%
- `identifier[].value`: 100.0%
- `location`: 100.0%
- `location.display`: 100.0%
- `location.reference`: 100.0%
- `numberOfInstances`: 100.0%
- `numberOfSeries`: 100.0%
- `procedureCode`: 100.0%
- `procedureCode[]`: 100.0%
- `procedureCode[].coding`: 100.0%
- `procedureCode[].coding[]`: 100.0%
- `procedureCode[].coding[].code`: 100.0%
- `procedureCode[].coding[].display`: 100.0%
- `procedureCode[].coding[].system`: 100.0%
- `procedureCode[].text`: 100.0%
- `resourceType`: 100.0%
- `series`: 100.0%
- `series[]`: 100.0%
- `series[].bodySite`: 100.0%
- `series[].bodySite.code`: 100.0%
- `series[].bodySite.display`: 100.0%
- `series[].bodySite.system`: 100.0%
- `series[].instance`: 100.0%
- `series[].instance[]`: 100.0%
- `series[].instance[].number`: 100.0%
- `series[].instance[].sopClass`: 100.0%
- `series[].instance[].sopClass.code`: 100.0%
- `series[].instance[].sopClass.system`: 100.0%
- `series[].instance[].title`: 100.0%
- `series[].instance[].uid`: 100.0%
- `series[].modality`: 100.0%
- `series[].modality.code`: 100.0%
- `series[].modality.display`: 100.0%
- `series[].modality.system`: 100.0%
- `series[].number`: 100.0%
- `series[].numberOfInstances`: 100.0%
- `series[].started`: 100.0%
- `series[].uid`: 100.0%
- `started`: 100.0%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%

## Immunization
**Bronze plan**: bronzed

- Source file: `Immunization.ndjson`
- Total records: 164146
- Sample size: 1000

### Schema Presence
- `encounter`: 100.0%
- `encounter.reference`: 100.0%
- `id`: 100.0%
- `location`: 100.0%
- `location.display`: 100.0%
- `location.reference`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `occurrenceDateTime`: 100.0%
- `patient`: 100.0%
- `patient.reference`: 100.0%
- `primarySource`: 100.0%
- `resourceType`: 100.0%
- `status`: 100.0%
- `vaccineCode`: 100.0%
- `vaccineCode.coding`: 100.0%
- `vaccineCode.coding[]`: 100.0%
- `vaccineCode.coding[].code`: 100.0%
- `vaccineCode.coding[].display`: 100.0%
- `vaccineCode.coding[].system`: 100.0%
- `vaccineCode.text`: 100.0%

## Location
**Bronze plan**: available-not-bronzed

- Source file: `Location.1778542031678.ndjson`
- Total records: 1142
- Sample size: 1000

### Schema Presence
- `address`: 100.0%
- `address.city`: 100.0%
- `address.country`: 100.0%
- `address.line`: 100.0%
- `address.line[]`: 100.0%
- `address.postalCode`: 100.0%
- `address.state`: 100.0%
- `id`: 100.0%
- `identifier`: 100.0%
- `identifier[]`: 100.0%
- `identifier[].system`: 100.0%
- `identifier[].value`: 100.0%
- `managingOrganization`: 100.0%
- `managingOrganization.display`: 100.0%
- `managingOrganization.identifier`: 100.0%
- `managingOrganization.identifier.system`: 100.0%
- `managingOrganization.identifier.value`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `name`: 100.0%
- `position`: 100.0%
- `position.latitude`: 100.0%
- `position.longitude`: 100.0%
- `resourceType`: 100.0%
- `status`: 100.0%
- `telecom`: 100.0%
- `telecom[]`: 100.0%
- `telecom[].system`: 100.0%
- `telecom[].value`: 100.0%

## Medication
**Bronze plan**: available-not-bronzed

- Source file: `Medication.ndjson`
- Total records: 203834
- Sample size: 1000

### Schema Presence
- `code`: 100.0%
- `code.coding`: 100.0%
- `code.coding[]`: 100.0%
- `code.coding[].code`: 100.0%
- `code.coding[].display`: 100.0%
- `code.coding[].system`: 100.0%
- `code.text`: 100.0%
- `id`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `resourceType`: 100.0%
- `status`: 100.0%

## MedicationAdministration
**Bronze plan**: available-not-bronzed

- Source file: `MedicationAdministration.ndjson`
- Total records: 203834
- Sample size: 1000

### Schema Presence
- `context`: 100.0%
- `context.reference`: 100.0%
- `dosage`: 0.2%
- `dosage.dose`: 0.2%
- `dosage.dose.value`: 0.2%
- `effectiveDateTime`: 100.0%
- `id`: 100.0%
- `medicationCodeableConcept`: 100.0%
- `medicationCodeableConcept.coding`: 100.0%
- `medicationCodeableConcept.coding[]`: 100.0%
- `medicationCodeableConcept.coding[].code`: 100.0%
- `medicationCodeableConcept.coding[].display`: 100.0%
- `medicationCodeableConcept.coding[].system`: 100.0%
- `medicationCodeableConcept.text`: 100.0%
- `reasonCode`: 29.8%
- `reasonCode[]`: 29.8%
- `reasonCode[].coding`: 29.8%
- `reasonCode[].coding[]`: 29.8%
- `reasonCode[].coding[].code`: 29.8%
- `reasonCode[].coding[].display`: 29.8%
- `reasonCode[].coding[].system`: 29.8%
- `reasonCode[].text`: 29.8%
- `reasonReference`: 58.0%
- `reasonReference[]`: 58.0%
- `reasonReference[].display`: 58.0%
- `reasonReference[].reference`: 58.0%
- `resourceType`: 100.0%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%

## MedicationRequest
**Bronze plan**: bronzed

- Source file: `MedicationRequest.ndjson`
- Total records: 573225
- Sample size: 1000

### Schema Presence
- `authoredOn`: 100.0%
- `category`: 100.0%
- `category[]`: 100.0%
- `category[].coding`: 100.0%
- `category[].coding[]`: 100.0%
- `category[].coding[].code`: 100.0%
- `category[].coding[].display`: 100.0%
- `category[].coding[].system`: 100.0%
- `category[].text`: 100.0%
- `dosageInstruction`: 69.9%
- `dosageInstruction[]`: 69.9%
- `dosageInstruction[].additionalInstruction`: 11.4%
- `dosageInstruction[].additionalInstruction[]`: 11.4%
- `dosageInstruction[].additionalInstruction[].coding`: 11.4%
- `dosageInstruction[].additionalInstruction[].coding[]`: 11.4%
- `dosageInstruction[].additionalInstruction[].coding[].code`: 11.4%
- `dosageInstruction[].additionalInstruction[].coding[].display`: 11.4%
- `dosageInstruction[].additionalInstruction[].coding[].system`: 11.4%
- `dosageInstruction[].additionalInstruction[].text`: 11.4%
- `dosageInstruction[].asNeededBoolean`: 69.9%
- `dosageInstruction[].doseAndRate`: 34.5%
- `dosageInstruction[].doseAndRate[]`: 34.5%
- `dosageInstruction[].doseAndRate[].doseQuantity`: 34.5%
- `dosageInstruction[].doseAndRate[].doseQuantity.value`: 34.5%
- `dosageInstruction[].doseAndRate[].type`: 34.5%
- `dosageInstruction[].doseAndRate[].type.coding`: 34.5%
- `dosageInstruction[].doseAndRate[].type.coding[]`: 34.5%
- `dosageInstruction[].doseAndRate[].type.coding[].code`: 34.5%
- `dosageInstruction[].doseAndRate[].type.coding[].display`: 34.5%
- `dosageInstruction[].doseAndRate[].type.coding[].system`: 34.5%
- `dosageInstruction[].sequence`: 69.9%
- `dosageInstruction[].text`: 46.8%
- `dosageInstruction[].timing`: 34.5%
- `dosageInstruction[].timing.repeat`: 34.5%
- `dosageInstruction[].timing.repeat.frequency`: 34.5%
- `dosageInstruction[].timing.repeat.period`: 34.5%
- `dosageInstruction[].timing.repeat.periodUnit`: 34.5%
- `encounter`: 100.0%
- `encounter.reference`: 100.0%
- `id`: 100.0%
- `intent`: 100.0%
- `medicationCodeableConcept`: 87.1%
- `medicationCodeableConcept.coding`: 87.1%
- `medicationCodeableConcept.coding[]`: 87.1%
- `medicationCodeableConcept.coding[].code`: 87.1%
- `medicationCodeableConcept.coding[].display`: 87.1%
- `medicationCodeableConcept.coding[].system`: 87.1%
- `medicationCodeableConcept.text`: 87.1%
- `medicationReference`: 12.9%
- `medicationReference.reference`: 12.9%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `reasonCode`: 19.9%
- `reasonCode[]`: 19.9%
- `reasonCode[].coding`: 19.9%
- `reasonCode[].coding[]`: 19.9%
- `reasonCode[].coding[].code`: 19.9%
- `reasonCode[].coding[].display`: 19.9%
- `reasonCode[].coding[].system`: 19.9%
- `reasonCode[].text`: 19.9%
- `reasonReference`: 53.1%
- `reasonReference[]`: 53.1%
- `reasonReference[].display`: 53.1%
- `reasonReference[].reference`: 53.1%
- `requester`: 100.0%
- `requester.display`: 100.0%
- `requester.reference`: 100.0%
- `resourceType`: 100.0%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%

## Observation
**Bronze plan**: bronzed

- Source file: `Observation.ndjson`
- Total records: 5862543
- Sample size: 1000

### Schema Presence
- `category`: 100.0%
- `category[]`: 100.0%
- `category[].coding`: 100.0%
- `category[].coding[]`: 100.0%
- `category[].coding[].code`: 100.0%
- `category[].coding[].display`: 100.0%
- `category[].coding[].system`: 100.0%
- `code`: 100.0%
- `code.coding`: 100.0%
- `code.coding[]`: 100.0%
- `code.coding[].code`: 100.0%
- `code.coding[].display`: 100.0%
- `code.coding[].system`: 100.0%
- `code.text`: 100.0%
- `component`: 9.5%
- `component[]`: 9.5%
- `component[].code`: 9.5%
- `component[].code.coding`: 9.5%
- `component[].code.coding[]`: 9.5%
- `component[].code.coding[].code`: 9.5%
- `component[].code.coding[].display`: 9.5%
- `component[].code.coding[].system`: 9.5%
- `component[].code.text`: 9.5%
- `component[].valueCodeableConcept`: 2.9%
- `component[].valueCodeableConcept.coding`: 2.9%
- `component[].valueCodeableConcept.coding[]`: 2.9%
- `component[].valueCodeableConcept.coding[].code`: 2.9%
- `component[].valueCodeableConcept.coding[].display`: 2.9%
- `component[].valueCodeableConcept.coding[].system`: 2.9%
- `component[].valueCodeableConcept.text`: 2.9%
- `component[].valueQuantity`: 9.5%
- `component[].valueQuantity.code`: 9.5%
- `component[].valueQuantity.system`: 9.5%
- `component[].valueQuantity.unit`: 9.5%
- `component[].valueQuantity.value`: 9.5%
- `component[].valueString`: 2.9%
- `effectiveDateTime`: 100.0%
- `encounter`: 100.0%
- `encounter.reference`: 100.0%
- `id`: 100.0%
- `issued`: 100.0%
- `meta`: 92.8%
- `meta.profile`: 92.8%
- `meta.profile[]`: 92.8%
- `resourceType`: 100.0%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%
- `valueCodeableConcept`: 6.9%
- `valueCodeableConcept.coding`: 6.9%
- `valueCodeableConcept.coding[]`: 6.9%
- `valueCodeableConcept.coding[].code`: 6.9%
- `valueCodeableConcept.coding[].display`: 6.9%
- `valueCodeableConcept.coding[].system`: 6.9%
- `valueCodeableConcept.text`: 6.9%
- `valueQuantity`: 83.6%
- `valueQuantity.code`: 83.6%
- `valueQuantity.system`: 83.6%
- `valueQuantity.unit`: 83.6%
- `valueQuantity.value`: 83.6%

## Organization
**Bronze plan**: bronzed

- Source file: `Organization.1778542031678.ndjson`
- Total records: 1141
- Sample size: 1000

### Schema Presence
- `active`: 100.0%
- `address`: 100.0%
- `address[]`: 100.0%
- `address[].city`: 100.0%
- `address[].country`: 100.0%
- `address[].line`: 100.0%
- `address[].line[]`: 100.0%
- `address[].postalCode`: 100.0%
- `address[].state`: 100.0%
- `extension`: 100.0%
- `extension[]`: 100.0%
- `extension[].url`: 100.0%
- `extension[].valueInteger`: 100.0%
- `id`: 100.0%
- `identifier`: 100.0%
- `identifier[]`: 100.0%
- `identifier[].system`: 100.0%
- `identifier[].value`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `name`: 100.0%
- `resourceType`: 100.0%
- `telecom`: 100.0%
- `telecom[]`: 100.0%
- `telecom[].system`: 100.0%
- `telecom[].value`: 100.0%
- `type`: 100.0%
- `type[]`: 100.0%
- `type[].coding`: 100.0%
- `type[].coding[]`: 100.0%
- `type[].coding[].code`: 100.0%
- `type[].coding[].display`: 100.0%
- `type[].coding[].system`: 100.0%
- `type[].text`: 100.0%

## Patient
**Bronze plan**: bronzed

- Source file: `Patient.ndjson`
- Total records: 11423
- Sample size: 1000

### Schema Presence
- `address`: 100.0%
- `address[]`: 100.0%
- `address[].city`: 100.0%
- `address[].country`: 100.0%
- `address[].extension`: 100.0%
- `address[].extension[]`: 100.0%
- `address[].extension[].extension`: 100.0%
- `address[].extension[].extension[]`: 100.0%
- `address[].extension[].extension[].url`: 100.0%
- `address[].extension[].extension[].valueDecimal`: 100.0%
- `address[].extension[].url`: 100.0%
- `address[].line`: 100.0%
- `address[].line[]`: 100.0%
- `address[].postalCode`: 100.0%
- `address[].state`: 100.0%
- `birthDate`: 100.0%
- `communication`: 100.0%
- `communication[]`: 100.0%
- `communication[].language`: 100.0%
- `communication[].language.coding`: 100.0%
- `communication[].language.coding[]`: 100.0%
- `communication[].language.coding[].code`: 100.0%
- `communication[].language.coding[].display`: 100.0%
- `communication[].language.coding[].system`: 100.0%
- `communication[].language.text`: 100.0%
- `deceasedDateTime`: 11.8%
- `extension`: 100.0%
- `extension[]`: 100.0%
- `extension[].extension`: 100.0%
- `extension[].extension[]`: 100.0%
- `extension[].extension[].url`: 100.0%
- `extension[].extension[].valueCoding`: 100.0%
- `extension[].extension[].valueCoding.code`: 100.0%
- `extension[].extension[].valueCoding.display`: 100.0%
- `extension[].extension[].valueCoding.system`: 100.0%
- `extension[].extension[].valueString`: 100.0%
- `extension[].url`: 100.0%
- `extension[].valueAddress`: 100.0%
- `extension[].valueAddress.city`: 100.0%
- `extension[].valueAddress.country`: 100.0%
- `extension[].valueAddress.state`: 100.0%
- `extension[].valueCode`: 100.0%
- `extension[].valueDecimal`: 100.0%
- `extension[].valueString`: 100.0%
- `gender`: 100.0%
- `id`: 100.0%
- `identifier`: 100.0%
- `identifier[]`: 100.0%
- `identifier[].system`: 100.0%
- `identifier[].type`: 100.0%
- `identifier[].type.coding`: 100.0%
- `identifier[].type.coding[]`: 100.0%
- `identifier[].type.coding[].code`: 100.0%
- `identifier[].type.coding[].display`: 100.0%
- `identifier[].type.coding[].system`: 100.0%
- `identifier[].type.text`: 100.0%
- `identifier[].value`: 100.0%
- `maritalStatus`: 100.0%
- `maritalStatus.coding`: 100.0%
- `maritalStatus.coding[]`: 100.0%
- `maritalStatus.coding[].code`: 100.0%
- `maritalStatus.coding[].display`: 100.0%
- `maritalStatus.coding[].system`: 100.0%
- `maritalStatus.text`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `multipleBirthBoolean`: 97.6%
- `multipleBirthInteger`: 2.4%
- `name`: 100.0%
- `name[]`: 100.0%
- `name[].family`: 100.0%
- `name[].given`: 100.0%
- `name[].given[]`: 100.0%
- `name[].prefix`: 80.5%
- `name[].prefix[]`: 80.5%
- `name[].suffix`: 1.4%
- `name[].suffix[]`: 1.4%
- `name[].use`: 100.0%
- `resourceType`: 100.0%
- `telecom`: 100.0%
- `telecom[]`: 100.0%
- `telecom[].system`: 100.0%
- `telecom[].use`: 100.0%
- `telecom[].value`: 100.0%
- `text`: 100.0%
- `text.div`: 100.0%
- `text.status`: 100.0%

### Patient Stats
- Gender distribution:
  - female: 499
  - male: 501
- Birth year decades:
  - 1910s: 11
  - 1920s: 19
  - 1930s: 6
  - 1940s: 58
  - 1950s: 89
  - 1960s: 135
  - 1970s: 137
  - 1980s: 126
  - 1990s: 131
  - 2000s: 123
  - 2010s: 102
  - 2020s: 63
- Deceased percentage: 11.8%

## Practitioner
**Bronze plan**: bronzed

- Source file: `Practitioner.1778542031678.ndjson`
- Total records: 1141
- Sample size: 1000

### Schema Presence
- `active`: 100.0%
- `address`: 100.0%
- `address[]`: 100.0%
- `address[].city`: 100.0%
- `address[].country`: 100.0%
- `address[].line`: 100.0%
- `address[].line[]`: 100.0%
- `address[].postalCode`: 100.0%
- `address[].state`: 100.0%
- `extension`: 100.0%
- `extension[]`: 100.0%
- `extension[].url`: 100.0%
- `extension[].valueInteger`: 100.0%
- `gender`: 100.0%
- `id`: 100.0%
- `identifier`: 100.0%
- `identifier[]`: 100.0%
- `identifier[].system`: 100.0%
- `identifier[].value`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `name`: 100.0%
- `name[]`: 100.0%
- `name[].family`: 100.0%
- `name[].given`: 100.0%
- `name[].given[]`: 100.0%
- `name[].prefix`: 100.0%
- `name[].prefix[]`: 100.0%
- `resourceType`: 100.0%
- `telecom`: 100.0%
- `telecom[]`: 100.0%
- `telecom[].extension`: 100.0%
- `telecom[].extension[]`: 100.0%
- `telecom[].extension[].url`: 100.0%
- `telecom[].extension[].valueBoolean`: 100.0%
- `telecom[].system`: 100.0%
- `telecom[].use`: 100.0%
- `telecom[].value`: 100.0%

## PractitionerRole
**Bronze plan**: available-not-bronzed

- Source file: `PractitionerRole.1778542031678.ndjson`
- Total records: 1141
- Sample size: 1000

### Schema Presence
- `code`: 100.0%
- `code[]`: 100.0%
- `code[].coding`: 100.0%
- `code[].coding[]`: 100.0%
- `code[].coding[].code`: 100.0%
- `code[].coding[].display`: 100.0%
- `code[].coding[].system`: 100.0%
- `code[].text`: 100.0%
- `id`: 100.0%
- `location`: 100.0%
- `location[]`: 100.0%
- `location[].display`: 100.0%
- `location[].identifier`: 100.0%
- `location[].identifier.system`: 100.0%
- `location[].identifier.value`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `organization`: 100.0%
- `organization.display`: 100.0%
- `organization.identifier`: 100.0%
- `organization.identifier.system`: 100.0%
- `organization.identifier.value`: 100.0%
- `practitioner`: 100.0%
- `practitioner.display`: 100.0%
- `practitioner.identifier`: 100.0%
- `practitioner.identifier.system`: 100.0%
- `practitioner.identifier.value`: 100.0%
- `resourceType`: 100.0%
- `specialty`: 100.0%
- `specialty[]`: 100.0%
- `specialty[].coding`: 100.0%
- `specialty[].coding[]`: 100.0%
- `specialty[].coding[].code`: 100.0%
- `specialty[].coding[].display`: 100.0%
- `specialty[].coding[].system`: 100.0%
- `specialty[].text`: 100.0%
- `telecom`: 100.0%
- `telecom[]`: 100.0%
- `telecom[].extension`: 100.0%
- `telecom[].extension[]`: 100.0%
- `telecom[].extension[].url`: 100.0%
- `telecom[].extension[].valueBoolean`: 100.0%
- `telecom[].system`: 100.0%
- `telecom[].use`: 100.0%
- `telecom[].value`: 100.0%

## Procedure
**Bronze plan**: bronzed

- Source file: `Procedure.ndjson`
- Total records: 1848211
- Sample size: 1000

### Schema Presence
- `code`: 100.0%
- `code.coding`: 100.0%
- `code.coding[]`: 100.0%
- `code.coding[].code`: 100.0%
- `code.coding[].display`: 100.0%
- `code.coding[].system`: 100.0%
- `code.text`: 100.0%
- `encounter`: 100.0%
- `encounter.reference`: 100.0%
- `id`: 100.0%
- `location`: 100.0%
- `location.display`: 100.0%
- `location.reference`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `performedPeriod`: 100.0%
- `performedPeriod.end`: 100.0%
- `performedPeriod.start`: 100.0%
- `reasonCode`: 8.0%
- `reasonCode[]`: 8.0%
- `reasonCode[].coding`: 8.0%
- `reasonCode[].coding[]`: 8.0%
- `reasonCode[].coding[].code`: 8.0%
- `reasonCode[].coding[].display`: 8.0%
- `reasonCode[].coding[].system`: 8.0%
- `reasonCode[].text`: 8.0%
- `reasonReference`: 43.6%
- `reasonReference[]`: 43.6%
- `reasonReference[].display`: 43.6%
- `reasonReference[].reference`: 43.6%
- `resourceType`: 100.0%
- `status`: 100.0%
- `subject`: 100.0%
- `subject.reference`: 100.0%

## Provenance
**Bronze plan**: available-not-bronzed

- Source file: `Provenance.ndjson`
- Total records: 11423
- Sample size: 1000

### Schema Presence
- `agent`: 100.0%
- `agent[]`: 100.0%
- `agent[].onBehalfOf`: 100.0%
- `agent[].onBehalfOf.display`: 100.0%
- `agent[].onBehalfOf.reference`: 100.0%
- `agent[].type`: 100.0%
- `agent[].type.coding`: 100.0%
- `agent[].type.coding[]`: 100.0%
- `agent[].type.coding[].code`: 100.0%
- `agent[].type.coding[].display`: 100.0%
- `agent[].type.coding[].system`: 100.0%
- `agent[].type.text`: 100.0%
- `agent[].who`: 100.0%
- `agent[].who.display`: 100.0%
- `agent[].who.reference`: 100.0%
- `id`: 100.0%
- `meta`: 100.0%
- `meta.profile`: 100.0%
- `meta.profile[]`: 100.0%
- `recorded`: 100.0%
- `resourceType`: 100.0%
- `target`: 100.0%
- `target[]`: 100.0%
- `target[].reference`: 100.0%

## SupplyDelivery
**Bronze plan**: available-not-bronzed

- Source file: `SupplyDelivery.ndjson`
- Total records: 297753
- Sample size: 1000

### Schema Presence
- `id`: 100.0%
- `occurrenceDateTime`: 100.0%
- `patient`: 100.0%
- `patient.reference`: 100.0%
- `resourceType`: 100.0%
- `status`: 100.0%
- `suppliedItem`: 100.0%
- `suppliedItem.itemCodeableConcept`: 100.0%
- `suppliedItem.itemCodeableConcept.coding`: 100.0%
- `suppliedItem.itemCodeableConcept.coding[]`: 100.0%
- `suppliedItem.itemCodeableConcept.coding[].code`: 100.0%
- `suppliedItem.itemCodeableConcept.coding[].display`: 100.0%
- `suppliedItem.itemCodeableConcept.coding[].system`: 100.0%
- `suppliedItem.itemCodeableConcept.text`: 100.0%
- `suppliedItem.quantity`: 100.0%
- `suppliedItem.quantity.value`: 100.0%
- `type`: 100.0%
- `type.coding`: 100.0%
- `type.coding[]`: 100.0%
- `type.coding[].code`: 100.0%
- `type.coding[].display`: 100.0%
- `type.coding[].system`: 100.0%
