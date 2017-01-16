#!/usr/bin/python

import boto
import boto.ec2
import time
import smtplib

# locate files
error_log = 'error.log'
journal_file = 'journal'

def stderrfunc(e, block):
    with open(error_log, 'a') as errlogs:
        errlogs.write(date + ' : ' + 'copyimage.py' + ' : ' + block + ' : ')
        errlogs.writelines(str(e))
        errlogs.write('\n' + '\n')
        global err
        err = True

def unexperrfunc(block):
    with open(error_log, 'a') as errlogs:
        errlogs.write(date + ' : copyimage.py(Unexpected Error) : ' + block + '\n')
        global err
        err=True

if __name__ == '__main__':

    img_dict = {}
    err = False
    date = time.strftime("%Y-%m-%d")
    conn = boto.ec2.connect_to_region('us-east-1')

    with open(journal_file, 'r') as journalf:
        for line in journalf:
            try:
                cimage = conn.copy_image(source_region='us-west-2', source_image_id=line[26:38], name=line[69:-1] + '-' + date)
                img_dict[line[26:38]] = cimage.image_id
            except BaseException as e:
                stderrfunc(e, 'Copy Image Block')
                img_dict[line[26:38]] = 'CopyImgError'
            except:
                unexperrfunc('Copy Image Block')
                img_dict[line[26:38]] = 'CopyImgError'

    with open(journal_file, 'r') as journalf:
        lines = journalf.readlines()
        for l in range(len(lines)):
            wimg_id = lines[l][26:38]
            if img_dict[wimg_id] != 'CopyImgError':
                try:
                    dereg = conn.deregister_image(lines[l][41:53])
                except BaseException as e:
                    stderrfunc(e, 'Deregister Image Block')
                except:
                    unexperrfunc('Deregister Image Block')
                lines[l] = lines[l][:41] + img_dict[wimg_id] + lines[l][53:]
                changes = open(journal_file, 'w')
                changes.writelines(lines)
                changes.close()

    '''if err:
    username = 'EMAIL@gmail.com'
    password = 'PASSWORD'
    toaddrs = 'EMAIL'
    msg = 'Error has been occured during copying'
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(username, toaddrs, msg)
    server.quit()'''

    # lines[l][:10] - date
    # lines[l][13:23] - west instance id
    # lines[l][26:38] - west image id
    # lines[l][41:53] - east image id
    # lines[l][56:66] - east instance id
    # lines[l][69:-1] - instance and image name
