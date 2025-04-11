clear; close all;
imaqreset; delete(serialportfind);

arduinoPort = 'COM4';
conexPort = 'COM3';

scannerControlGUI(arduinoPort,conexPort);

function scannerControlGUI(arduinoPort,conexPort)

load('excitation_profile.mat','profile_488','profile_565');

%% control the camera

% Create figure
fig = figure('Toolbar','none',...
       'Menubar', 'none',...
       'NumberTitle','Off',...
       'Name','Camera Control and Live View',...
       'CloseRequestFcn', @closeGUI,...
       'Position',[100,100,1200,800]);

% axis diagram
axes('Unit', 'pixels', 'Position',[970 150 120 120]); hold on;
xlim([0,1]);
ylim([0,1]);
quiver(.1,.9,.8,0,'LineWidth',1,'MaxHeadSize',.5,'AutoScale','off','Color','k');
quiver(.1,.9,0,-.8,'LineWidth',1,'MaxHeadSize',.5,'AutoScale','off','Color','k');
text(.1,.08,'X','FontSize',15,'HorizontalAlignment','center','VerticalAlignment','top');
text(.92,.9,'Y','FontSize',15,'HorizontalAlignment','left','VerticalAlignment','middle');
set(gca,'visible','off');

uicontrol('Style', 'text', 'String', 'Camera control', 'FontSize', 15, 'FontWeight', 'bold',...
          'Position', [50, 200, 200, 50], 'HorizontalAlignment', 'center');

% Define the video input object
vid = videoinput('tisimaq_r2013_64','DMK 72BUC02', 'Y800 (2592x1944)');
src = getselectedsource(vid);
set(vid,'TriggerRepeat',inf);

% Configure the video input object
vid.FramesPerTrigger = 2;
triggerconfig(vid, 'manual');
   
% Create UI controls
% Gain control
uicontrol('Parent', fig, 'Style','text', 'Position',[65 180 100 30], 'String','Gain','FontSize',12,'HorizontalAlignment','left');
hGain = uicontrol('Parent', fig, 'Style','edit', 'Position',[185 180 80 30], 'String','4','FontSize',12);

% Exposure control
uicontrol('Parent', fig, 'Style','text', 'Position',[65 150 100 30], 'String','Exposure (s)','FontSize',12,'HorizontalAlignment','left');
hExposure = uicontrol('Parent', fig, 'Style','edit', 'Position',[185 150 80 30], 'String','0.1','FontSize',12);

% Start button
uicontrol('Parent', fig, 'Style','pushbutton', 'Position',[65 100 80 40], 'String','Start',...
          'Callback', @(src,event)startAcquisition(), 'FontSize',12);
      
% Stop button
uicontrol('Parent', fig, 'Style','pushbutton', 'Position',[155 100 80 40], 'String','Stop',...
          'Callback', @(src,event)stopAcquisition(), 'FontSize',12);

% Axes for displaying the image
hAxes = axes('Unit', 'pixels', 'Position',[300 300 500 375]);

% Initialize the image handle
hImage = image(zeros(2592,1944), 'Parent', hAxes);
% axis(hAxes, 'image');
colormap gray;
set(gca,'xtick',[],'ytick',[])

% Function to start acquisition
function startAcquisition
    gain = str2double(get(hGain, 'String'));
    exposure = str2double(get(hExposure, 'String'));
    
    % Set camera properties
    src.Gain = gain;
    src.Exposure = exposure;
    
    % Start video preview
    preview(vid, hImage);

    axis image;

end

% Function to stop acquisition
function stopAcquisition
    stoppreview(vid);
end

%% laser shutter

% Add a button for Laser On/Off
uicontrol('Style', 'text', 'String', '488 laser', 'FontSize', 15, 'FontWeight', 'bold',...
          'Position', [850, 650, 80, 50], 'HorizontalAlignment', 'center');
uicontrol('Style', 'pushbutton', 'String', 'off',...
          'Position', [930, 650, 80, 50], 'FontSize', 15, 'FontWeight', 'bold',...
          'Callback', @laser488Off);
uicontrol('Style', 'pushbutton', 'String', 'on',...
          'Position', [1010, 650, 80, 50], 'FontSize', 15, 'FontWeight', 'bold',...
          'Callback', @laser488On);

uicontrol('Style', 'text', 'String', '565 LED', 'FontSize', 15, 'FontWeight', 'bold',...
          'Position', [850, 580, 80, 50], 'HorizontalAlignment', 'center');
uicontrol('Style', 'pushbutton', 'String', 'off',...
          'Position', [930, 580, 80, 50], 'FontSize', 15, 'FontWeight', 'bold',...
          'Callback', @laser568Off);
uicontrol('Style', 'pushbutton', 'String', 'on',...
          'Position', [1010, 580, 80, 50], 'FontSize', 15, 'FontWeight', 'bold',...
          'Callback', @laser568On);

function laser568Off(src, event)
    writeline(arduino, 'b');
end

function laser568On(src, event)
    writeline(arduino, 'a');
end

function laser488Off(src, event)
    writeline(arduino, 'd');
end

function laser488On(src, event)
    writeline(arduino, 'c');
end


%% arduino for x and y movements

xMax = 240;
yMax = 140;

uicontrol('Style', 'text', 'String', 'XY stage control', 'FontSize', 15, 'FontWeight', 'bold',...
          'Position', [50, 650, 200, 50], 'HorizontalAlignment', 'center');

% Initialize Arduino connection
arduino = serialport(arduinoPort, 9600); % Adjust COM port as needed
configureTerminator(arduino, "CR/LF");
flush(arduino);

% Step size input
txtStepSize = uicontrol('Style', 'edit', 'String', '1', 'FontSize', 12, ...
                        'Position', [185, 620, 50, 30], 'BackgroundColor', 'white');
uicontrol('Style', 'text', 'String', 'Step size (mm)', 'FontSize', 12, ...
          'Position', [65, 620, 120, 30], 'HorizontalAlignment', 'left');

% Direction buttons
uicontrol('Style', 'pushbutton', 'String', '↑', 'FontSize', 12, ...
          'Position', [125, 560, 50, 50], 'Callback', {@moveCallback, 'up', arduino});
uicontrol('Style', 'pushbutton', 'String', '↓', 'FontSize', 12, ...
          'Position', [125, 460, 50, 50], 'Callback', {@moveCallback, 'down', arduino});
uicontrol('Style', 'pushbutton', 'String', '←', 'FontSize', 12, ...
          'Position', [75, 510, 50, 50], 'Callback', {@moveCallback, 'left', arduino});
uicontrol('Style', 'pushbutton', 'String', '→', 'FontSize', 12, ...
          'Position', [175, 510, 50, 50], 'Callback', {@moveCallback, 'right', arduino});

% Step size input
txtStepSize = uicontrol('Style', 'edit', 'String', '1', 'FontSize', 12, ...
                        'Position', [185, 620, 50, 30], 'BackgroundColor', 'white');
uicontrol('Style', 'text', 'String', 'Step size (mm)', 'FontSize', 12, ...
          'Position', [65, 620, 120, 30], 'HorizontalAlignment', 'left');

% Store components for easy access
fig.UserData.txtStepSize = txtStepSize;
fig.UserData.arduino = arduino;

% record current XY position
xPosText = uicontrol('Style', 'text', 'Position', [300, 230, 150, 30], 'String', 'Current X (mm)', 'FontSize',12, 'HorizontalAlignment', 'left');
xDisplay = uicontrol('Style', 'text', 'Position', [450, 230, 90, 30], 'String', '0', 'FontSize',12, 'HorizontalAlignment', 'right');
yPosText = uicontrol('Style', 'text', 'Position', [300, 200, 150, 30], 'String', 'Current Y (mm)', 'FontSize',12, 'HorizontalAlignment', 'left');
yDisplay = uicontrol('Style', 'text', 'Position', [450, 200, 90, 30], 'String', '0', 'FontSize',12, 'HorizontalAlignment', 'right');

bypassXYlimitCheckBox = uicontrol('Style','checkbox','Position',[300,80,240,30],'String','Bypass xy limit','FontSize',12,'Value',0);

if exist('currentPos.mat','file') == 2
    load currentPos.mat;
else
    currentX = 0;
    currentY = 0;
end

homeButtonXY = uicontrol('Style', 'pushbutton', 'Position', [300, 140, 150, 40], 'String', 'Home XY', 'Callback', @homeMotorXY, 'FontSize',12);

function homeMotorXY(~,~)
    currentX = 0;
    currentY = 0;
    xDisplay.String = num2str(currentX);
    yDisplay.String = num2str(currentY);
end

function moveCallback(src, ~, direction, arduino)
    fig = ancestor(src, 'figure');
    txtStepSize = fig.UserData.txtStepSize;
    stepSizeStr = txtStepSize.String;
    stepSize = str2double(stepSizeStr) * 32; % Convert mm to steps
    if isnan(stepSize)
        warndlg('Step size must be a number.', 'Input Error');
        return;
    end
    
    % Generate command string based on direction
    commandStr = '';
    switch direction
        case 'left'
            commandStr = ['-' num2str(stepSize) 'y'];
            dxy = [-1,0];
        case 'right'
            commandStr = [num2str(stepSize) 'y'];
            dxy = [1,0];
        case 'up'
            commandStr = ['-' num2str(stepSize*1.5) 'x'];
            dxy = [0,1];
        case 'down'
            commandStr = [num2str(stepSize*1.5) 'x'];
            dxy = [-0,-1];
    end
    
    nextX = currentX + dxy(1)*str2double(stepSizeStr);
    nextY = currentY + dxy(2)*str2double(stepSizeStr);
    
    bypassXYlimit = get(bypassXYlimitCheckBox,'Value');
    if (nextX>=0 && nextX<=xMax && nextY>=0 && nextY<=yMax)||bypassXYlimit
        currentX = nextX;
        currentY = nextY;
        xDisplay.String = num2str(currentX);
        yDisplay.String = num2str(currentY);
        writeline(arduino, commandStr);
    end
end

%% conex-cc
uicontrol('Style', 'text', 'String', 'Z stage control', 'FontSize', 15, 'FontWeight', 'bold',...
          'Position', [50, 380, 200, 50], 'HorizontalAlignment', 'center');

% Load the Newport CONEX-CC library
currentFolder = pwd; % Assuming the DLL is in the current working directory
dllPath = fullfile(currentFolder, 'Newport.CONEXCC.CommandInterface.dll');
NET.addAssembly(dllPath);

% Create the motor controller object
CC = CommandInterfaceConexCC.ConexCC();
CC.OpenInstrument(conexPort);

% Current Z position display
zPosText = uicontrol('Style', 'text', 'Position', [65, 320, 80, 30], 'String', 'Current Z', 'FontSize',12, 'HorizontalAlignment', 'left');
zDisplay = uicontrol('Style', 'text', 'Position', [145, 320, 90, 30], 'String', '0', 'FontSize',12, 'HorizontalAlignment', 'right');

% Step size input
stepSizeText = uicontrol('Style', 'text', 'Position', [65, 350, 120, 30], 'String', 'Step size (mm)', 'FontSize',12, 'HorizontalAlignment', 'left');
stepSizeEdit = uicontrol('Style', 'edit', 'Position', [185, 350, 50, 30], 'String', '1', 'FontSize',12);

% Control buttons
upButton = uicontrol('Style', 'pushbutton', 'Position', [65, 280, 50, 40], 'String', 'Up', 'Callback', {@moveMotor, 'up'}, 'FontSize',12);
downButton = uicontrol('Style', 'pushbutton', 'Position', [125, 280, 50, 40], 'String', 'Down', 'Callback', {@moveMotor, 'down'}, 'FontSize',12);
homeButton = uicontrol('Style', 'pushbutton', 'Position', [185, 280, 50, 40], 'String', 'Home', 'Callback', @homeMotor, 'FontSize',12);

% Function to move motor
function moveMotor(~, ~, direction)
    stepSize = str2double(stepSizeEdit.String);
    [~, currentZ, ~] = CC.TP(1);
    
    if strcmp(direction, 'up')
        newZ = currentZ + stepSize;
    else
        newZ = currentZ - stepSize;
    end
    
    CC.PA_Set(1, newZ);
    pause(.1); % Wait for the motor to move
    updateZPosition();
end

function homeMotor(~,~)
    CC.OR(1);
    pause(1); % Wait for the motor to move
end

% Function to update Z position display
function updateZPosition()
    [~, currentZ, ~] = CC.TP(1);
    zDisplay.String = num2str(currentZ);
end

% Initialize Z position display
updateZPosition();

%% 3D (x,y,t) scan
% Add 4D Scan button
zScanButton = uicontrol('Style', 'pushbutton', 'String', 'Scan', 'FontSize', 12, ...
                        'Position', [850, 430, 240, 40], 'Callback', @captureZScan, 'FontSize',12);
% Saved File Name Input
uicontrol('Style', 'text', 'Position', [850, 390, 120, 30], 'String', 'File Name:', 'FontSize',12, 'HorizontalAlignment', 'left');
fileNameEdit = uicontrol('Style', 'edit', 'Position', [970, 390, 120, 30], 'String', 'data', 'FontSize',12);

% time parameters
% capture interval
uicontrol('Style', 'text', 'Position', [850, 360, 120, 30], 'String', 'Δt (min):', 'FontSize',12, 'HorizontalAlignment', 'left');
tIntervalEdit = uicontrol('Style', 'edit', 'Position', [970, 360, 120, 30], 'String', '60', 'FontSize',12);

% number of timepoints
uicontrol('Style', 'text', 'Position', [850, 330, 120, 30], 'String', '# timepoints:', 'FontSize',12, 'HorizontalAlignment', 'left');
numTimepointsEdit = uicontrol('Style', 'edit', 'Position', [970, 330, 120, 30], 'String', '48', 'FontSize',12);

% xy parameters
% X Range Input
uicontrol('Style', 'text', 'Position', [850, 240, 120, 30], 'String', 'X Range (mm):', 'FontSize',12, 'HorizontalAlignment', 'left');
xRangeEdit = uicontrol('Style', 'edit', 'Position', [850, 210, 60, 30], 'String', '30', 'FontSize',12);

% Y Range Input
uicontrol('Style', 'text', 'Position', [950, 270, 120, 30], 'String', 'Y Range (mm):', 'FontSize',12, 'HorizontalAlignment', 'left');
yRangeEdit = uicontrol('Style', 'edit', 'Position', [1070, 270, 60, 30], 'String', '30', 'FontSize',12);

% XY Step Input
uicontrol('Style', 'text', 'Position', [850, 90, 120, 30], 'String', 'XY Step (mm):', 'FontSize',12, 'HorizontalAlignment', 'left');
xyStepEdit = uicontrol('Style', 'edit', 'Position', [970, 90, 120, 30], 'String', '3', 'FontSize',12);

function captureZScan(~, ~)

    pathName = 'C:\Data\';

    writeline(arduino, 'b');
    writeline(arduino, 'd');
    fileName = get(fileNameEdit, 'String');

    % t parameters
    tInterval = str2double(get(tIntervalEdit, 'String'))*60;
    numTimepoints = str2double(get(numTimepointsEdit, 'String'));

    % xy parameters
    xRange = str2double(get(xRangeEdit, 'String'));
    yRange = str2double(get(yRangeEdit, 'String'));
    xyStep = str2double(get(xyStepEdit, 'String'));

    xSlices = ceil(xRange/xyStep);
    ySlices = ceil(yRange/xyStep);

    numImgCaptured = 0;

    imageStack = zeros(389,389,xSlices*ySlices,2,'uint8');
    
    % loop through all timepoints
    for t = 1:numTimepoints
        startTimepoint = tic;
        imgMaxVal = 0;
        % loop through all xy positions
        numImgCaptured_t = 0;
        for xNum = 1:xSlices
            for yNum = 1:ySlices

                for excitationLine = 1:2
                    if excitationLine == 1
                        writeline(arduino, 'c'); %488
                    else
                        writeline(arduino, 'a'); %568
                    end

                    start(vid);
                    trigger(vid);
                    while get(vid,'FramesAvailable') < 2
                        unavailable = 1;
                    end
                    imageDataTmp = getdata(vid, 2);
                    stop(vid);
                    imageData = imageDataTmp(:,:,1,2);
                    imageData = medfilt2(imageData,[3,3]);
                    imageData = imresize(imageData,.2);
                    imgMaxVal = max([imgMaxVal,prctile(double(imageData(:)),95)]);

                    imagesc(imageData); % Display captured image
                    clim([0,255]);
                    colormap gray;
                    set(gca,'xtick',[],'ytick',[]);
                    imageData = imageData(:,11:end-120);

                    if rem((numImgCaptured+1),4000) == 1
                        imwrite(imageData,[pathName,fileName,'_',num2str(excitationLine),'_',num2str(ceil((numImgCaptured+1)/4000)),'.tif']);
                    else
                        imwrite(imageData,[pathName,fileName,'_',num2str(excitationLine),'_',num2str(ceil((numImgCaptured+1)/4000)),'.tif'], 'WriteMode','append');
                    end

                    if excitationLine == 1
                        imageData = uint8(double(imageData).*double(profile_488));
                        imageStack(:,:,numImgCaptured_t+1,1) = imageData;
                    else
                        imageData = uint8(double(imageData).*double(profile_565));
                        imageStack(:,:,numImgCaptured_t+1,2) = imageData;
                    end

                    numImgCaptured = numImgCaptured + 1;
                    if excitationLine == 2
                        numImgCaptured_t = numImgCaptured_t + 1;
                    end
                    if excitationLine == 1
                        writeline(arduino, 'd');
                    else
                        writeline(arduino, 'b');
                    end
                end
            
                if yNum ~= ySlices
                    if rem(xNum,2)
                        moveStage('right', xyStep, arduino);
                    else
                        moveStage('left', xyStep, arduino);
                    end
                    pause(1);
                elseif xNum ~= xSlices
                    moveStage('down', xyStep, arduino);
                    pause(1.5);
                end
            end
        end

        if rem(xSlices,2)
            yShift = -xyStep*(ySlices-1);
        else
            yShift = 0;
        end
        xShift = -xyStep*(xSlices-1);
        moveStage('left', abs(yShift), arduino);
        moveStage('up', abs(xShift), arduino);

        pause((abs(xShift)+abs(yShift))/400*30+2); % travel speed is ~30s for 400 mm

        writeline(arduino, 'b');
        writeline(arduino, 'd');

        imgFull = stitchImage(imageStack,xyStep,xSlices,ySlices);
        imwrite(imgFull(:,:,1),[pathName,fileName,'_1_stitch_',num2str(ceil(numImgCaptured/8000)),'.tif'], 'WriteMode','append');
        imwrite(imgFull(:,:,2),[pathName,fileName,'_2_stitch_',num2str(ceil(numImgCaptured/8000)),'.tif'], 'WriteMode','append');

        exposureList(t) = src.Exposure;
        save([pathName,fileName,'_exposureList.mat'],'exposureList');

        if imgMaxVal>200
            src.Exposure = src.Exposure/2;
        end
        
        acquisitionTime = toc(startTimepoint);
        pause(tInterval - acquisitionTime);
    end
end

function moveStage(direction, stepSizeMM, arduino)

    stepSize = stepSizeMM * 32;
    
    % Generate command string based on direction
    commandStr = '';
    switch direction
        case 'left'
            commandStr = ['-' num2str(stepSize) 'y'];
            dxy = [-1,0];
        case 'right'
            commandStr = [num2str(stepSize) 'y'];
            dxy = [1,0];
        case 'up'
            commandStr = ['-' num2str(stepSize*1.5) 'x'];
            dxy = [0,1];
        case 'down'
            commandStr = [num2str(stepSize*1.5) 'x'];
            dxy = [-0,-1];
    end

    nextX = currentX + dxy(1)*stepSizeMM;
    nextY = currentY + dxy(2)*stepSizeMM;
    
    if nextX>=0 && nextX<=xMax && nextY>=0 && nextY<=yMax
        currentX = nextX;
        currentY = nextY;
        xDisplay.String = num2str(currentX);
        yDisplay.String = num2str(currentY);
        writeline(arduino, commandStr);
    end

end

%% close GUI
% Clean up function
function closeGUI(src, event)
    writeline(arduino, 'b');
    writeline(arduino, 'd');
    delete(vid);
    CC.CloseInstrument();
    delete(fig);
    delete(arduino);
    save('currentPos.mat','currentX','currentY');
end

end
