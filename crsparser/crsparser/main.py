from parse import Parser
import filter

def main():
    Parser.load_dept_list("depts.txt")
    depts = Parser.parse_catalog("data.txt")
    for d in depts:
        print "\n-----", str(d), "-----"
        for c in d.courses:
            print str(c)
            for lec in c.lec_list:
                print "   " + str(lec)

if __name__ == "__main__":
    main()
