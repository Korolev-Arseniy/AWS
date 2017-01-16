#!/usr/bin/python

import boto
import boto.ec2
import time
import smtplib
import email.mime.multipart as emmult
import email.mime.text as emtext

# locate files
instance_file = 'instances'
error_log = 'error.log'
journal_file = 'journal'

def sendmail(sendfile, subject):
    username = 'EMAIL@gmail.com'
    password = 'PASSWORD'
    toaddrs = 'EMAIL'
    msg = emmult.MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = username
    msg['To'] = toaddrs
    file = open(sendfile, 'rb')
    attach = emtext.MIMEText(file.read(), 'text/txt;name="journal.txt"', 'utf-8')
    file.close()
    msg.attach(attach)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(username, toaddrs, msg.as_string())
    server.quit()

def stderrfunc(e, block):
    with open(error_log, 'a') as errlogs:
        errlogs.write(date + ' : ' + 'createimage.py' + ' : ' + block + ' : ')
        errlogs.writelines(str(e))
        errlogs.write('\n' + '\n')
        global err
        err = True

def unexperrfunc(block):
    with open(error_log, 'a') as errlogs:
        errlogs.write(date + ' : createimage.py(Unexpected Error) : ' + block + '\n')
        global err
        err = True

if __name__ == '__main__':

    logdict = {}
    instances_names = {}
    instances = []
    date = time.strftime("%Y-%m-%d")
    err = False

    with open(instance_file, 'r') as instancesf:
        for i in instancesf:
            if i not in instances:
                instances.append(i[:-1])

    with open(journal_file, 'r') as journalf:
        for i in journalf:
            if i[13:23] in instances and date <= i[:10]:
                instances.remove(i[13:23])

    conn = boto.ec2.connect_to_region('us-west-2')

    try:
        reservations = conn.get_all_instances(instance_ids=instances)
        for res in reservations:
            for inst in res.instances:
                instances_names[inst.id] = inst.tags['Name']
    except BaseException as e:
        stderrfunc(e, 'Instance Tags Block')
    except:
        unexperrfunc('Instance Tags Block')

    for instance in instances:
        try:
            id = conn.create_image(instance_id=instance, name=instances_names[instance]+'-'+date, description=instance+'-backup-'+date, no_reboot=True)
            logdict[instance] = id
        except BaseException as e:
            stderrfunc(e, 'Create Image Block')
            logdict[instance] = 'CreateImgErr'
        except:
            unexperrfunc('Create Image Block')
            logdict[instance] = 'CreateImgErr'

    with open(journal_file, 'r+') as f:
        lines = f.readlines()
        for l in range(len(lines)):
            instance = lines[l][13:23]
            if instance in instances and logdict[instance] != 'CreateImgErr':
                try:
                    dereg = conn.deregister_image(lines[l][26:38])
                except BaseException as e:
                    stderrfunc(e, 'Journal Block')
                except:
                    unexperrfunc('Journal Block')
                lines[l] = date + ' : ' + instance + ' : ' + logdict[instance] + lines[l][38:]
                changes = open(journal_file, 'w')
                changes.writelines(lines)
                changes.close()
            if instance in instances:
                instances.remove(instance)
        if instances:
            changes = open(journal_file, 'a')
            for instance in instances:
                changes.write(date+' : '+instance+' : ' + logdict[instance]+' :              :            : ' + instances_names[instance]+'\n')
            changes.close()

    if err:
        sendmail(error_log, 'Error has been occured! Please check log')
    else:
        sendmail(journal_file, 'Script complete')

    # lines[l][:10] - date
    # lines[l][13:23] - west instance id
    # lines[l][26:38] - west image id
    # lines[l][41:53] - east image id
    # lines[l][56:66] - east instance id
    # lines[l][69:-1] - instance and image name
