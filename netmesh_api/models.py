import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone as timezone
from django.core.validators import MaxValueValidator, MinValueValidator

from netmesh_api import choices


class UserProfile(models.Model):
    """ UserProfiles extend the default Django User models
        specifically to represent users who will be able to log-in
        on the Netmesh results server website
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    timezone = models.CharField(max_length=50, default='Asia/Manila',
                                choices=choices.timezone_choices)
    role = models.CharField(max_length=20, default='Cloud Admin')
    # Added for Password Expiry
    last_pwd_update = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'netmesh_api_userprofile'
        verbose_name = 'UserProfile'
        verbose_name_plural = 'UserProfiles'
        ordering = ['-id']

    def __str__(self):
        return "%s's profile" % self.user

    def display_name(self):
        if self.user.get_short_name():
            return self.user.get_short_name()
        else:
            return self.user.username


class AgentProfile(models.Model):
    """ Extension of the User model specifically for the test clients (aka  Agents)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    ntc_region = models.CharField(max_length=20, choices=choices.ntc_region_choices, default='unknown')
    device = models.CharField(max_length=20, choices=choices.device_choices, default='computer')
    registration_status = models.CharField(max_length=20, choices=choices.registration_choices, default='unregistered')

    def __str__(self):
        return "%s" % self.user

    def display_name(self):
        if self.user.get_short_name():
            return self.user.get_short_name()
        else:
            return self.user.username


class Server(models.Model):
    """ Model for a NetMesh test server """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    nickname = models.CharField(max_length=200, null=True)
    ip_address = models.GenericIPAddressField()  # assumes that server has a fixed IP address
    type = models.CharField(max_length=20, choices=choices.server_choices, default='unknown')
    lat = models.FloatField(default=16.647322, validators=[MaxValueValidator(90.0), MinValueValidator(-90.0)])
    long = models.FloatField(default=121.071959, validators=[MaxValueValidator(180.0), MinValueValidator(-180.0)])
    city = models.CharField(max_length=200, null=True)
    province = models.CharField(max_length=200, null=True)
    country = models.CharField(max_length=200, default='Philippines')
    sponsor = models.CharField(max_length=200, default='SponsorName')  # organization that hosts this server
    hostname = models.URLField(max_length=500, default="http://dummyhostname.com")

    def __str__(self):
        return "Server %s (%s)" % (self.nickname, self.uuid)


class Test(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(AgentProfile, null=False, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=False, protocol='IPv4')  # IP addr of agent when test was conducted
    test_type = models.CharField(null=False, max_length=50, choices=choices.test_type_choices)
    date_created = models.DateTimeField(auto_now_add=True)
    network_connection = models.CharField(max_length=20, choices=choices.network_choices, default='unknown')
    pcap = models.CharField(max_length=100, null=True)
    lat = models.FloatField(default=16.647322, validators=[MaxValueValidator(90.0), MinValueValidator(-90.0)])
    long = models.FloatField(default=121.071959, validators=[MaxValueValidator(180.0), MinValueValidator(-180.0)])
    mode = models.CharField(null=False, max_length=50, choices=choices.test_mode_choices, default='unknown')

    def __str__(self):
        return "Test %s" % self.id


class DataPoint(models.Model):
    """Model for a data point which is acquired by the test client against a test server"""
    date_tested = models.DateTimeField(blank=True, default=timezone.now)
    test_id = models.ForeignKey(Test, null=False, on_delete=models.CASCADE)
    direction = models.CharField(null=False, max_length=10, choices=choices.direction_choices, default='unknown')
    server = models.ForeignKey(Server, null=False, on_delete=models.CASCADE)
    path_mtu = models.IntegerField(null=True)  # Path Max Transmit Unit, in bytes
    baseline_rtt = models.FloatField(null=True)  # Baseline Round Trip Time, in ms
    bottleneck_bw = models.FloatField(null=True)  # Bottleneck Bandwidth, in Mbps
    bdp = models.FloatField(null=True)  # Bandwidth Delay Product, in bits
    min_rwnd = models.FloatField(null=True)  # Minimum Receive Window Size, in Kbytes
    ave_tcp_tput = models.FloatField(null=True)  # Average TCP Throughput, in Mbps
    ideal_tcp_tput = models.FloatField(null=True)  # Ideal TCP throughput, in Mbps
    actual_transfer_time = models.FloatField(null=True)  # Actual Transfer Time, in secs
    ideal_transfer_time = models.FloatField(null=True)  # Ideal Transfer Time, in secs
    tcp_ttr = models.FloatField(null=True)  # TCP transfer Time Ratio, unitless
    trans_bytes = models.FloatField(null=True)  # Transmitted Bytes, in bytes
    retrans_bytes = models.FloatField(null=True)  # Retransmitted Bytes, in bytes
    tcp_eff = models.FloatField(null=True)  # TCP Efficiency, in %
    ave_rtt = models.FloatField(null=True)  # Average Round Trip Time, in ms
    buffer_delay = models.FloatField(null=True)  # Buffer Delay, in %


class Traceroute(models.Model):
    date = models.DateTimeField(default=timezone.now)
    origin_ip = models.GenericIPAddressField(null=False)
    dest_ip = models.GenericIPAddressField(null=False)
    dest_name = models.CharField(max_length=200, null=False)


class Hop(models.Model):
    traceroute = models.ForeignKey(Traceroute, null=False, on_delete=models.CASCADE)
    hop_index = models.IntegerField(null=False)
    time1 = models.FloatField(null=True)
    time2 = models.FloatField(null=True)
    time3 = models.FloatField(null=True)
    host_name = models.CharField(max_length=200)  # domain name or fallback to IP address if no domain name
    host_ip = models.GenericIPAddressField(null=True)


class Speedtest(models.Model):
    date = models.DateTimeField(default=timezone.now)
    test_id = models.UUIDField(null=False, editable=False, unique=True)
    sid = models.CharField(max_length=32, null=False, editable=False)
    ip_address = models.GenericIPAddressField(null=False)
    # server = models.ForeignKey(Server, on_delete=models.CASCADE)
    rtt = models.FloatField(null=False)
    upload_speed = models.FloatField(null=False)
    download_speed = models.FloatField(null=False)
