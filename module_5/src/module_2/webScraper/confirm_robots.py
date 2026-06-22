'''Confirm robots.txt file from Grad Cafe'''


from urllib import parse, robotparser
def confirm_robot(base_url):
    '''Read robots.txt file from GradCafe.com and assess access to websites'''
    # ===========================
    # Verify robot.txt compliance
    # ===========================
    #stefan: FIX ACCESS TO ROBOTS
    agent = "*" #all agents
    robot_parser = robotparser.RobotFileParser()
    robot_parser.set_url(parse.urljoin(base_url,'robots.txt'))
    robot_parser.read()

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
        test_url = parse.urljoin(base_url,test_path)
        print(f"{robot_parser.can_fetch(agent, test_url), test_url}")

confirm_robot("https://www.thegradcafe.com")
