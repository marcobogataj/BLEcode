received_data = nicla_received;
sent_data = table2array(nicla_sent);

figure
plot(received_data(:,1),received_data(:,2),sent_data(:,1),sent_data(:,2))
grid on
xlabel('time [s]')
ylabel('Temperature [C°]')
legend('received data','sent data')
title('Compare sent and received data')

figure
plot(received_data(:,1)-sent_data(1:end-1,1))
grid on
xlabel('sample index [/]')
ylabel('Delay [s]')

figure
plot(received_data(:,2)-sent_data(1:end-1,2))
grid on
xlabel('sample index [/]')
ylabel('Error [C°]')