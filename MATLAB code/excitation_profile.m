clear; close all;
img = double(imread('488_profile.tif'));
profile_488 = medfilt2(imresize(img,.2),[20,20]);
profile_488(end,:) = profile_488(end-1,:);
profile_488 = profile_488(:,11:end-120);
profile_488 = min(profile_488(:))./profile_488;
subplot(1,2,1);
imagesc(profile_488);
clim([0,1]);
axis image;

img = double(imread('568_profile.tif'));
profile_565 = medfilt2(imresize(img,.2),[20,20]);
profile_565(end,:) = profile_565(end-1,:);
profile_565 = profile_565(:,11:end-120);
profile_565 = min(profile_565(:))./profile_565;
subplot(1,2,2);
imagesc(profile_565);
clim([0,1]);
axis image;

imwrite(uint8(profile_488*255),'profile_470.bmp');
imwrite(uint8(profile_565*255),'profile_565.bmp');
