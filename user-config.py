# This is an automatically generated file. You can find more
# configuration parameters in 'config.py' file or refer
# https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.config.html

# The family of sites to be working on.
# Pywikibot will import families/xxx_family.py so if you want to change
# this variable, you have to ensure that such a file exists. You may use
# generate_family_file to create one.
mylang = 'commons'
family_files['commons'] = 'https://commons.moegirl.org.cn/api.php'
family = 'commons'

# The site code (language) of the site to be working on.

# The dictionary usernames should contain a username for each site where you
# have a bot account. If you have a unique username for all sites of a
# family , you can use '*'
usernames['commons']['*'] = 'PetraMagna'
password_file = "user-password.py"

minthrottle = 0
maxthrottle = 60

# Slow down the robot such that it never makes a second page edit within
# 'put_throttle' seconds.
put_throttle = 10  # type: Union[int, float]
