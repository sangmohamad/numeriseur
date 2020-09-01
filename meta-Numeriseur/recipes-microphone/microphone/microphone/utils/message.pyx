import re
import utils.directives as directives
import utils.result_codes as result_codes

class Message(object):
    '''
    An RTSP message parser / container
    '''

    PROTOCOL = 'RTSP/1.0'
    SEQUENCE_FIELD = 'CSeq: '
    CONTENT_LENGTH = 'Content-Length: '
    TRANSPORT = "Transport: "
    SESSION = "Session: "
    NEWLINE = '\r\n'

    def __init__(self, sequence):
        '''
        Creates a new message with the given sequence number
        '''
        self.sequence = sequence


class RequestMessage(Message):
    '''
    An RTSP Request message
    '''

    def __init__(self, directive=None, sequence=0, uri=None, transport=None):

        self.directive = directive
        self.sequence = sequence
        self.uri = uri
        self.transport = transport

        Message.__init__(self, self.sequence)


    def parse_header(self, message):
        '''
        Extract the directive
        '''
        try:
            parameters = re.match('([A-Z_]+)\s+(.+)\s+(RTSP/1.0)', message)

            return parameters.group(1, 2, 3)
        except AttributeError as e:
            print ("Failed to parse request header line")
            raise e


    def parse_sequence_number(self, message):
        '''
        Extract the sequence number
        '''
        try:
            return int(re.search(self.SEQUENCE_FIELD + '(\d+)', message).group(1))
        except AttributeError as e:
            print ("Failed to parse sequence")
            raise e

    def parse_client_ports(self, message):
        '''
        Parse the client ports from the message
        '''
        try:
            parsed_transport_field = re.search(self.TRANSPORT + '.*client_port=(\d+)-(\d+)', message)
            return int(parsed_transport_field.group(1)), int(parsed_transport_field.group(2))
        except AttributeError as e:
            return (None, None)

    def parse(self, message):
        '''
        Parses the given request into its different fields
        '''
        try:
            message_fields = message.split(self.NEWLINE)

            if (len(message_fields) == 0):
                return False

            self.directive, self.uri, self.version = self.parse_header(message_fields[0])

            self.sequence = self.parse_sequence_number(message)

            self.client_rtp_port, self.client_rtcp_port = self.parse_client_ports(message)

            return True

        except BaseException as parse_error:
            print ("Parse error: ", parse_error)
            print ("Originated from: '%s'" % message)
            return False


    def _generate_header(self):
        '''
        Generate the RTSP message header
        '''
        if (self.uri is not None):
            return '{} {}'.format(self.directive, self.uri)
        else:
            return self.directive

    def __str__(self):
        '''
        Overriding the __str__ - converts all message fields to a string
        '''
        fields = [self._generate_header(),
                  self.SEQUENCE_FIELD + str(self.sequence)]

        if (self.transport is not None):
            fields.append(self.TRANSPORT + self.transport)

        return '\n\r'.join(fields)


class ResponseMessage(Message):
    '''
    An RTSP Response message
    '''

    def __init__(self, sequence, result,session_id, additional_fields=[], content_lines=[]):
        self.result = result
        self.additional_fields = additional_fields
        self.content_lines = content_lines
        self.session_id=session_id

        Message.__init__(self, sequence)

    def __str__(self):
        # Create the response by joining the basic structure together
        # with the additional_fields and the content issued by the inheriting class


        



        response_field = f'%s %d %s' % (self.PROTOCOL,
                                       self.result,
                                       result_codes.strings[self.result])

        sequence_field =f"{self.SEQUENCE_FIELD + str(self.sequence)}"
        session_id=f"Session: {self.session_id}"

        content_length = sum([len(content_line) for content_line in self.content_lines])
        content_length_field =f"{self.CONTENT_LENGTH + str(content_length)}" 

        # Basic RTSP message structure
        message = [response_field,
                   sequence_field,
                   session_id,
                   content_length_field]

        # All the fields the specific message needs
        message.extend(self.additional_fields)

        # There is content attached to the message
        if (content_length > 0):
            message.append('')
            message.extend(self.content_lines)

        # Finalizing newline of the RTSP response
        message.append(self.NEWLINE)

        return (self.NEWLINE).join(message)

    def get_deterministic_payload(self):
        '''
        Used for unittesting - return only the fields which are a part of the comparison criteria.
        For example, fields such as date are generated at runtime and cannot be predicted.
        '''
        pass

    def compare_deterministics(self, other_message):
        '''
        True - match
        False - don't match
        '''
        my_deter_payload = self.get_deterministic_payload()
        other_deter_payload = other_message.get_deterministic_payload()

        if (len(my_deter_payload) != len (other_deter_payload)):
            raise ValueError(len(my_deter_payload) + '!=' + len(other_deter_payload))

        line_changes = []
        for line_number in range(len(my_deter_payload)):
            if (my_deter_payload[line_number] !=
                other_deter_payload[line_number]):
                line_changes.append((my_deter_payload[line_number], other_deter_payload[line_number]))

        if (len(line_changes) > 0):
            raise ValueError('\n' + '\n'.join([str(change) for change in line_changes]))

        return True

class OptionsResponseMessage(ResponseMessage):
    '''
    An RTSP OPTIONS response
    '''
    def __init__(self, sequence,session_id, result):
        payload = ["Public: %s,%s,%s,%s,%s,%s" %
                            (directives.DESCRIBE,
                             directives.SETUP,
                             directives.TEARDOWN,
                             directives.PLAY,
                             directives.PAUSE,
                             directives.GET_PARAMETER)]

        ResponseMessage.__init__(self, sequence=sequence,
                                 result=result,session_id=session_id,
                                 additional_fields=payload)

class DescribeResponseMessage(ResponseMessage):
    '''
    An RTSP DESCRIBE response
    '''
    def __init__(self,
                 sequence,session_id,
                 result,
                 date=None,
                 server_uri=None,
                 sdp_o_param=None):




        server_ip = server_uri

        sdp_fields = [ 'v=0',
                       'o=- {time} {time} IN IP4 {ip}'.format(time=sdp_o_param, ip=server_ip),
                       's=Unnamed',
                       'i=N/A',
                       'c=IN IP4 0.0.0.0',
                       't=0 0',
                       'a=tool:vlc 2.0.8',
                       'a=recvonly',
                       'a=type:unicast',
                       'a=charset:UTF-8',
                       'a=control:%s' % server_uri,
                       'a=rtpmap:96 H264/90000',
                       'a=fmtp:96 packetization-mode=1;profile-level-id=64001f;sprop-parameter-sets=Z2QAH6zZgLQz+sBagQEAoAAAfSAAF3AR4wYzQA==,aOl4fLIs;',
                       'm=audio 0 RTP/AVP 8',
                       'b=RR:0',
                        ]

        payload = ['Server: VLC/2.0.8',
                   'Date: %s' % date,
                   'Content-Type: application/sdp',
                   'Content-Base: %s' % server_uri,
                   'Cache-Control: no-cache']

        ResponseMessage.__init__(self, sequence=sequence,
                                 result=result,session_id=session_id,
                                 additional_fields=payload,
                                 content_lines=sdp_fields)

    def get_deterministic_payload(self):
        deter_payload = [payload_line
                         for payload_line in (self.additional_fields + self.content_lines)
                         if (not payload_line.startswith('Date') and
                             not payload_line.startswith('o=-'))]
        return deter_payload

class SetupResponseMessage(ResponseMessage):
    '''
    An RTSP SETUP response
    '''
    def __init__(self,
                 sequence,session_id,
                 result,
                 client_rtp_port,
                 session):

        payload = [self.TRANSPORT +
                    "RTP/AVP/UDP;unicast;client_port={}".format(client_rtp_port),
                   self.SESSION + str(session)]

        ResponseMessage.__init__(self,
                                 sequence=sequence,
                                 result=result,session_id=session_id,
                                 additional_fields=payload)

    def get_deterministic_payload(self):
        deter_payload = [payload_line
                         for payload_line in (self.additional_fields + self.content_lines)
                         if (not payload_line.startswith(self.TRANSPORT) and
                             not payload_line.startswith(self.SESSION))]

        return deter_payload
