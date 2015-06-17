import argparse
import collections
import HTSeq


def find_type_idattr_pairs(gff_file):
    gtf_file = HTSeq.GFF_Reader(gff_file, end_included=True)

    types = collections.Counter()
    attribute_keys = collections.Counter()
    count = 0
    for feature in gtf_file:
        types[feature.type] += 1
        for key in feature.attr:
            attribute_keys[(feature.type, key)] += 1
        count += 1

    for type in sorted(types):
        print "type:", type, "   found", types[type], "values"
        for key in sorted(attribute_keys):
            if key[0] == type:
                print "\tidattr:", key[1],
                if attribute_keys[key] == types[type]:
                    print ""
                else:
                    print "    Only", attribute_keys[key], "Values found!"
        print

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("gff_file",
                        help="Path to gff file to check. ")
    args = parser.parse_args()
    find_type_idattr_pairs(args.gff_file)
