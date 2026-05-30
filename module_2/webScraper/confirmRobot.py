from urllib import parse, robotparser
def confirmRobot(BASE_URL):
    # The number of pages on thegradcafe.com we want to scrape
    numPages = 10

    # ===========================
    # Verify robot.txt compliance
    # ===========================

    # STEFAN. THIS HAS BUGS. I'M NOT SURE WHY THIS IS SAYING 

    agent = "*" #all
    robotParser = robotparser.RobotFileParser()
    robotParser.set_url(parse.urljoin(BASE_URL,'robots.txt'))
    robotParser.read();

    # look through the following paths to see if we have access there
    paths = [
        "/signin",
        "/register",
        "/forgot-password",
        "/signin",
        "/register",
        "/forgot-password",
        "/reset-password",
        "/confirm-password",
        "/verify-email",
        "/profile",
        "/survey"
    ]

    for test_path in paths:
        test_url = parse.urljoin(BASE_URL,test_path)
        print(f"{robotParser.can_fetch(agent, test_url), test_url}")