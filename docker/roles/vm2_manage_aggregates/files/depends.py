import yaml, re, copy
from optparse import OptionParser

def set_resource_dependency(data, resource, prevresource, track_index):
  depend_resource = "delay_" + resource
  data['resources'][depend_resource] = {}
  data['resources'][depend_resource]['type'] = "Ericsson::Heat::DelayPolicy"
  data['resources'][depend_resource]['properties'] = {}
  data['resources'][depend_resource]['properties']['delay'] = {}
  data['resources'][depend_resource]['properties']['delay'] = 0
  data['resources'][resource]['depends_on'] = depend_resource
  if prevresource[track_index] <> "": 
    data['resources'][depend_resource]['depends_on'] = prevresource[track_index]
  prevresource[track_index] = resource

def main():
  parser = OptionParser()
  parser.add_option("-f", "--file", dest="inputfilename",
                  help="input FILE", metavar="FILE")
  parser.add_option("-o", "--output", dest="outputfilename",
                  help="write result to FILE", metavar="FILE")
  parser.add_option("-t", "--tracks", dest="tracks", default=1,
                  help="parallel track", metavar="Integer")
  parser.add_option("-i", "--includefilter", dest="includefilter", default="^.*$",
                  help="inclusion filter", metavar="String")

  (options, args) = parser.parse_args()

  stream = open(options.inputfilename, 'r')
  data = yaml.load(stream)
  prevresource = []

  for i in range(0, int(options.tracks)):
    prevresource.append( "" )

  tracks = int(options.tracks)
  resource_number = 0

  data_result = copy.deepcopy(data)

  for resource in data['resources'] :
    if data['resources'][resource]['type'] == "OS::Cinder::Volume" and 'depends_on' not in data['resources'][resource] and re.match(options.includefilter, resource) and (re.match("^.*_mn_.*", resource) or re.match(".*_mon_.*", resource)):
      set_resource_dependency(data_result, resource, prevresource, resource_number % tracks)
      resource_number = resource_number + 1

  for resource in data['resources'] :
    if data['resources'][resource]['type'] == "OS::Cinder::Volume" and 'depends_on' not in data['resources'][resource] and re.match(options.includefilter, resource) and not re.match(".*_mn_.*", resource) and not re.match(".*_mon_.*", resource):
      set_resource_dependency(data_result, resource, prevresource, resource_number % tracks)
      resource_number = resource_number + 1
  with open(options.outputfilename, 'w') as yaml_file:
    yaml_file.write( yaml.dump(data_result, default_flow_style=False))

main()



