-- phpMyAdmin SQL Dump
-- version 4.4.10
-- http://www.phpmyadmin.net
--
-- Client :  localhost:8889
-- Généré le :  Mar 25 Avril 2017 à 12:50
-- Version du serveur :  5.5.42
-- Version de PHP :  7.0.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Base de données :  `projet_blog_p3`
--

-- --------------------------------------------------------

--
-- Structure de la table `billets`
--

CREATE TABLE `billets` (
  `id` int(11) NOT NULL,
  `image` varchar(255) NOT NULL,
  `alt` varchar(71) NOT NULL,
  `titre` varchar(255) NOT NULL,
  `contenu` text NOT NULL,
  `auteur` varchar(70) NOT NULL,
  `date_creation` datetime NOT NULL
) ENGINE=MyISAM AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;

--
-- Contenu de la table `billets`
--

INSERT INTO `billets` (`id`, `image`, `alt`, `titre`, `contenu`, `auteur`, `date_creation`) VALUES
(1, '/OPENCLASSROOM/PHP/P3/app/frontend/images/c-1.jpg', '', 'Chapitre I: Découvrez l''Alaska !', 'L’Alaska est immense : 3 800 km d’est en ouest, 2 300 km du nord au sud, soit 3 fois la France pour bien moins d’un million d’habitants, mais aussi 150 000 orignaux, 110 000 ours noirs, 100 000 glaciers et 35 000 grizzlys. Ce sont les Aléoutes qui ont donné son nom à l’Alaska - un nom à sa mesure, signifiant « grande terre » ou « continent ».\r\n\r\n \r\n', 'Jean Forteroche', '2010-03-25 16:28:41'),
(2, '/OPENCLASSROOM/PHP/P3/app/frontend/images/c-2.jpg', '', 'Chapitre II: La conquête des Russes!', 'Pour les Russes qui conquirent la région au XIXe siècle, c’était un grand réservoir de fourrures. Pour les Américains qui vinrent ensuite, l’espoir d’un nouvel enrichissement rapide, dans les placers (plages de graviers) des rivières aurifères. Gold ! Dans les années 1900, le mot s’affichait régulièrement dans tous les journaux de l’hémisphère nord, attirant des bordées d’immigrants emplis d’espoir. C’est ainsi que l’Alaska se peupla et gagna son surnom actuel : la « dernière frontière ».\r\n ', 'Jean Forteroche', '2010-03-27 18:31:11'),
(5, '/OPENCLASSROOM/PHP/P3/app/frontend/images/c-3.jpg', '', 'Chapitre III: Un espace préservé', 'Ce bout du continent n’a longtemps vécu que pour être exploité. Pourtant, dès 1980, le président Carter mit en réserve d’un trait de plume 40 millions d’hectares de terres vierges pour les générations futures. Les débats furent houleux mais tous, aujourd’hui, apprécient ces espaces préservés.\r\n', 'Jean Forteroche', '2017-03-21 10:14:00'),
(6, '/OPENCLASSROOM/PHP/P3/app/frontend/images/c-4.jpg', '', 'Chapitre IV: Le mont McKinley!', 'De l’emblématique mont McKinley (6 194 m) aux glaciers bleutés se déversant dans le Prince William Sound, des plages sauvages de l’île de Kodiak aux forêts profondes de l’île Amirauté, domaine des ours, des saumons et des aigles chauves, c’est la nature que l’on vient rencontrer en Alaska. Une nature dont la virginité n’a que peu d’égale. Une nature où s’évanouissent tous les bruits du monde développé.\r\n', 'Jean Forteroche', '2017-03-24 08:30:00'),
(7, '/OPENCLASSROOM/PHP/P3/app/frontend/images/c-5.jpg', '', 'Chapitre V: La rué vers l''or.', 'Appelée aussi ruée vers l''or du Yukon, la ruée vers l''or du Klondike, aux frontières de l''Alaska et du Canada, attira environ 100 000 prospecteurs entre 1896 et 1899. Les prospecteurs avaient commencé à chercher de l''or dans le Yukon dès les années 1880. La découverte d''importants dépôts le long de la rivière Klondike le 16 août 1896 fut accueillie avec enthousiasme, lorsque les nouvelles arrivèrent à San Francisco l''année suivante. Dans un premier temps, l''isolement de la région et le climat extrême empêchèrent la transmission des informations jusqu''à l''année suivante. La ruée commença avec l''arrivée de chargements d''or d''une valeur totale de 1 139 000 $ (plus d''un milliard de dollars actuels) dans les ports de la côte Ouest des États-Unis en juillet 1897. Cependant, le trajet vers le nord, avec de lourdes charges, à travers le terrain difficile, se révéla trop dur pour de nombreux prospecteurs, surtout ceux qui n''avais pris leur précaution face au climat froid. De 30 000 à 40 000 candidats à la fortune arrivèrent sur place, une fraction des intéressés, et environ 4 000 trouvèrent de l''or. La ruée se termina en 1899 lorsque de l''or fut découvert à Nome en Alaska et de nombreux prospecteurs quittèrent le Klondike. La ruée a été immortalisée par des livres comme L''Appel de la forêt et des films tels que La Ruée vers l''or.', 'Jean Forteroche', '2017-03-24 08:21:00');

--
-- Index pour les tables exportées
--

--
-- Index pour la table `billets`
--
ALTER TABLE `billets`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT pour les tables exportées
--

--
-- AUTO_INCREMENT pour la table `billets`
--
ALTER TABLE `billets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=9;