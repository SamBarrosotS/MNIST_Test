import time
import matplotlib.pyplot as plt
import torch
import torchvision
from torchmetrics import MetricCollection, Accuracy, Precision, Recall, F1Score, FBetaScore, ROC, AUROC
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import os


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)

    n_epochs = 3
    batch_size_train = 64
    batch_size_test = 64
    learning_rate = 0.01
    momentum = 0.2
    log_interval = 10

    random_seed = 1
    torch.backends.cudnn.enabled = False
    torch.manual_seed(random_seed)

    train_loader = torch.utils.data.DataLoader(
        torchvision.datasets.MNIST('./files/', train=True, download=True,
            transform=torchvision.transforms.Compose([
                torchvision.transforms.ToTensor(),
                torchvision.transforms.Normalize(
                    (0.1307,), (0.3081,))
                ])),
        batch_size=batch_size_train, shuffle=True, pin_memory=True, num_workers=4)
    
    test_loader = torch.utils.data.DataLoader(
        torchvision.datasets.MNIST('./files/', train=False, download=True,
            transform=torchvision.transforms.Compose([
                torchvision.transforms.ToTensor(),
                torchvision.transforms.Normalize(
                    (0.1307,), (0.3081,))
                ])),
        batch_size=batch_size_test, pin_memory=True, num_workers=4)
    
    examples = enumerate(test_loader)
    batch_idx, (example_data, example_targets) = next(examples)

    example_data.shape

    network = Net()
    network.to(device)
    optimizer = optim.SGD(network.parameters(), lr=learning_rate, momentum=momentum)
    
    metric_collection = MetricCollection({
        'acc': Accuracy(task = 'multiclass', num_classes=10).to(device),
        'prec': Precision(num_classes=10, average='macro', task = 'multiclass').to(device),
        'rec': Recall(num_classes=10, average='macro', task = 'multiclass').to(device),
        'F1': F1Score(task = 'multiclass', num_classes=10).to(device),
        'FB': FBetaScore(beta=0.5, task = 'multiclass', num_classes=10).to(device),
        'AUROC': AUROC(task = 'multiclass', num_classes=10).to(device),
        'ROC': ROC(task = 'multiclass', num_classes=10).to(device)
    })

    """
    train_losses = []
    train_counter = []
    test_losses = []
    test_counter = [i*len(train_loader.dataset) for i in range(1, n_epochs+1)]
    """

    for epoch in range(1, n_epochs + 1):
        #Train
        network.train()
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = network(data).to(device)
            batch_metrics = metric_collection.forward(output,target)
            loss = F.nll_loss(output, target)
            loss.backward()
            optimizer.step()
            if batch_idx % log_interval == 0:
                print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                    epoch, batch_idx * len(data), len(train_loader.dataset),
                    100. * batch_idx / len(train_loader), loss.item()))
                """
                train_losses.append(loss.item())
                train_counter.append(
                    (batch_idx*64) + ((epoch-1)*len(train_loader.dataset)))
                """
                if not os.path.exists("./results"):
                    os.makedirs("./results")
                torch.save(network.state_dict(), './results/model.pth')
                torch.save(optimizer.state_dict(), './results/optimizer.pth')
        
        val_metrics = metric_collection.compute()
        print(f'Metrics on all data: {val_metrics}')

        #Test
        network.eval()
        test_loss = 0
        correct = 0
        with torch.no_grad():
            for data, target in test_loader:
                data, target = data.to(device), target.to(device)
                output = network(data)
                """
                test_loss += F.nll_loss(output, target, size_average=False).item()
                pred = output.data.max(1, keepdim=True)[1]
                correct += pred.eq(target.data.view_as(pred)).sum()
                """
        """
        test_loss /= len(test_loader.dataset)
        test_losses.append(test_loss)
        print('\nTest set: Avg. loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
            test_loss, correct, len(test_loader.dataset),
            100. * correct / len(test_loader.dataset)))
        """
    """
    fig = plt.figure()
    plt.plot(train_counter, train_losses, color='blue')
    plt.plot(test_counter,test_losses, color='red')
    plt.legend(['Train Loss', 'Test Loss'], loc='upper right')
    plt.xlabel('number of training examples seen')
    plt.ylabel('negative log likelihood loss')
    plt.show()
    """

    print("-------------------")
    print(val_metrics['ROC'][0])
    print("-------------------")
    print(len(val_metrics['ROC'][0][0]))
    #for a in range(0,len(val_metrics['ROC'][0][0])):
        #print(val_metrics['ROC'][0][0][a])
    print("-------------------")
    print(val_metrics['ROC'][0][0][0])
    print("-------------------")

    x_val=[]
    for i in range(0,len(val_metrics['ROC'][0][0])):
        x_val.append(i/len(val_metrics['ROC'][0][0]))
    for i in range(0,len(x_val)):
        x_val[i].to(device)
    plt.plot(x_val,val_metrics['ROC'][0][0])
    plt.show()








class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x)



"""
def train(epoch):
    network.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        optimizer.zero_grad()
        output = network(da)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                100. * batch_idx / len(train_loader), loss.item()))
            train_losses.append(loss.item())
            train_counter.append(
                (batch_idx*64) + ((epoch-1)*len(train_loader.dataset)))
            torch.save(network.state_dict(), './results/model.pth')
            torch.save(optimizer.state_dict(), './results/optimizer.pth')
"""

"""
def test():
    network.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            output = network(data)
            test_loss += F.nll_loss(output, target, size_average=False).item()
            pred = output.data.max(1, keepdim=True)[1]
            correct += pred.eq(target.data.view_as(pred)).sum()
    test_loss /= len(test_loader.dataset)
    test_losses.append(test_loss)
    print('\nTest set: Avg. loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct / len(test_loader.dataset)))
"""






if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))

