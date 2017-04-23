<?php 
//modele : Acces au donnes
/******** GERE PAR LE MANAGER ***********/
try
{
	$bdd = new PDO('mysql:host=localhost;dbname=projet_blog_p3;charset=utf8', 'root', 'root');
}
catch (Exception $e)
{
        die('Erreur : ' . $e->getMessage());
}
$query = "SELECT * FROM billets ORDER BY date_creation, name";
$req =$bdd->prepare($query);
$req->execute();
// PDO::FETCH_ASSOC = retourne un tableau indexé par le nom de la colonne comme retourné dans le jeu de résultats
while ($row = $req->fetch(PDO::FETCH_ASSOC)) {
	
	$billet = array(
		'id'=> $row['id'],
		'image'=> $row['image'],
		'alt'=> $row['alt'],
		'titre'=> $row['titre'],
		'contenu'=> $row['contenu'],
		'auteur'=> $row['auteur'],
		'date_creation'=> $row['date_creation'],
	);
	//creation objet $billet 
{
      $touslesbillets[] = new Billet($donnees);
}
    return $touslesbillets;
  }
/*********** fin du manager **********/
$manager = new BilletManager();
$billets = $manager->getAll();
//traitement 
//vue
;?>

	<!DOCTYPE html>
	<html>

	<!-- on récupere le headers  -->
	<?php include_once("header.php"); ?>



		<body>


			<?php include_once("header_top.php"); ?>

				<?php include_once("menu.php"); ?>

					<?php include_once("banner.php"); ?>

						<?php include ("container_corps.php"); ?>

							<?php include_once("footer.php"); ?>

								<?php include ("script.php"); ?>


		</body>

	</html>