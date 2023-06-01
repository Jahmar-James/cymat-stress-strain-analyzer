from docx import Document

doc = Document()

doc.add_heading('Test Report', 0)

sections = {
    'a': 'Nature and designation of the product being tested',
    'b': 'Material and density of the sample',
    'c': 'Type of sampling',
    'd': 'Dimensions of the samples in mm, giving the ratio of side length to height',
    'e': 'Number of samples',
    'f': 'Test conditions (temperature, humidity)',
    'g': 'Type of testing machines and measuring range of the measuring equipment',
    'h': 'Compression speed(s) in s-1',
    'i': 'Plateau stress Rplt',
    'j': 'Compression at plateau end AAt / start of compression range',
    'k': 'Gradient of the elastic straight line m',
    'l': 'Energy absorption Ev',
    'm': 'Energy absorption efficiency Eff',
    'n': 'Upper compressive yield strength ReH',
    'o': 'Offset yield strength Rp1',
    's': 'a stress/strain diagram with characteristic values in each case',
    't': 'any deviations from this standard',
    'u': 'the test date'
}

for key in sections:
    doc.add_heading(sections[key], level=1)
    doc.add_paragraph('...')  # Placeholder

doc.save('test_report.docx')
